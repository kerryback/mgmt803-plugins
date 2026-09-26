"""
FastAPI app that generates a sample children's picture book -- a short set of
plot beats (page text) and a matching illustration for each page -- from
character, art-style, and moral-of-the-story inputs entered in a form.

Plot beats (text) go through OpenRouter chat completions via the `openai`
client, exactly like the other OpenRouter apps in this workspace. Illustrations
go through OpenRouter's separate image endpoint
(POST https://openrouter.ai/api/v1/images) via `requests`, since that endpoint
is not reachable through the openai client's images.generate() -- that method
targets OpenAI's own /images/generations path, which OpenRouter does not
implement. Page 1's illustration is generated first and then passed back as an
input_reference on every later page's image request, so the same
character/art style anchors the rest of the book instead of drifting page to
page.

Run with:
    uvicorn book_app:app --host 0.0.0.0 --port 8000
"""
import base64
import json
import os
import re
import threading
import time
import uuid
from io import BytesIO
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from openai import OpenAI
from PIL import Image as PILImage
from pydantic import BaseModel, Field
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

load_dotenv("env.txt", override=True)
assert os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY not set — check env.txt has an 'OPENAI_API_KEY=' line"

client = OpenAI(base_url="https://openrouter.ai/api/v1")  # OPENAI_API_KEY (OpenRouter)
TEXT_MODEL = "openai/gpt-4o-mini"
IMAGE_MODEL = "google/gemini-3.1-flash-image"
IMAGES_URL = "https://openrouter.ai/api/v1/images"

DATA_DIR = Path("data/childrens_books")
DATA_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = DATA_DIR / "manifest.json"

FILENAME_RE = re.compile(r"^page_\d{2}\.png$")

app = FastAPI()
jobs: dict[str, dict] = {}


class BookRequest(BaseModel):
    character_name: str
    character_description: str
    art_style: str
    moral: str
    setting: str = ""
    age_range: str = ""
    supporting_characters: str = ""
    tone: str = ""
    num_pages: int = Field(6, ge=4, le=30)
    rhyming: bool = False


def _read_manifest() -> list[dict]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return []


def _write_manifest(entries: list[dict]) -> None:
    MANIFEST_PATH.write_text(json.dumps(entries, indent=2))


def _generate_beats(req: BookRequest) -> dict:
    prompt = f"""Write a short children's picture book.

Main character: {req.character_name} — {req.character_description}
Art style for illustrations: {req.art_style}
Moral of the story: {req.moral}
Setting: {req.setting or "your choice"}
Target age range: {req.age_range or "young children"}
Supporting characters: {req.supporting_characters or "none required"}
Tone/mood: {req.tone or "warm and gentle"}
Number of pages: {req.num_pages}
Writing style: {"Write every page's text as rhyming verse (consistent rhyme scheme, e.g. AABB, read it aloud to check the rhythm)." if req.rhyming else "Write every page's text as simple prose, no rhyming."}

Return ONLY JSON with this exact shape, no other text:
{{
  "title": "book title",
  "pages": [
    {{"page_text": "1-3 simple sentences for this page", "illustration_prompt": "a vivid visual description of this page's scene, for an image generator"}}
  ]
}}
The "pages" array must have exactly {req.num_pages} entries. The last page's
text should land the moral naturally, without stating it as a lesson
explicitly.
"""
    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    pages = data["pages"][: req.num_pages]
    return {"title": data.get("title") or f"{req.character_name}'s Story", "pages": pages}


def _generate_image(prompt: str, reference_b64: str | None) -> bytes:
    body = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "aspect_ratio": "4:3",
        "output_format": "png",
    }
    if reference_b64:
        body["input_references"] = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{reference_b64}"}}
        ]
    r = requests.post(
        IMAGES_URL,
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json=body,
        timeout=120,
    )
    r.raise_for_status()
    return base64.b64decode(r.json()["data"][0]["b64_json"])


def _run_job(job_id: str, req: BookRequest) -> None:
    try:
        jobs[job_id]["progress"] = "writing the story"
        book = _generate_beats(req)
        pages = book["pages"]

        book_dir = DATA_DIR / job_id
        images_dir = book_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        style_prefix = (
            f"{req.art_style} children's book illustration. "
            f"Main character {req.character_name}: {req.character_description}. "
        )
        reference_b64 = None
        page_results = []
        for i, page in enumerate(pages, start=1):
            jobs[job_id]["progress"] = f"illustrating page {i} of {len(pages)}"
            filename = f"page_{i:02d}.png"
            try:
                image_bytes = _generate_image(style_prefix + page["illustration_prompt"], reference_b64)
                (images_dir / filename).write_bytes(image_bytes)
                if reference_b64 is None:
                    reference_b64 = base64.b64encode(image_bytes).decode()
                page_results.append({"page_text": page["page_text"], "image_file": filename, "image_failed": False})
            except Exception as e:
                page_results.append(
                    {"page_text": page["page_text"], "image_file": None, "image_failed": True, "error": str(e)}
                )

        result = {
            "book_id": job_id,
            "title": book["title"],
            "moral": req.moral,
            "character_name": req.character_name,
            "pages": page_results,
        }
        (book_dir / "story.json").write_text(json.dumps({**result, "inputs": req.model_dump()}, indent=2))

        manifest = _read_manifest()
        manifest.append(
            {
                "book_id": job_id,
                "title": book["title"],
                "character_name": req.character_name,
                "num_pages": len(pages),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        _write_manifest(manifest)

        jobs[job_id] = {"status": "done", "progress": "done", "result": result}
    except Exception as e:
        jobs[job_id] = {"status": "error", "progress": str(e), "result": None}


@app.post("/generate")
def generate(req: BookRequest):
    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {"status": "running", "progress": "queued", "result": None}
    threading.Thread(target=_run_job, args=(job_id, req), daemon=True).start()
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "unknown job_id")
    return job


@app.get("/books")
def list_books():
    return list(reversed(_read_manifest()))


@app.get("/books/{book_id}")
def get_book(book_id: str):
    if not book_id.isalnum():
        raise HTTPException(404, "unknown book_id")
    story_path = DATA_DIR / book_id / "story.json"
    if not story_path.exists():
        raise HTTPException(404, "unknown book_id")
    data = json.loads(story_path.read_text())
    return {
        "book_id": data["book_id"],
        "title": data["title"],
        "moral": data["moral"],
        "character_name": data["character_name"],
        "pages": data["pages"],
    }


@app.get("/books/{book_id}/images/{filename}")
def get_image(book_id: str, filename: str):
    if not book_id.isalnum() or not FILENAME_RE.match(filename):
        raise HTTPException(404, "image not found")
    path = DATA_DIR / book_id / "images" / filename
    if not path.exists():
        raise HTTPException(404, "image not found")
    return FileResponse(path)


def _build_pdf(data: dict, images_dir: Path) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BookTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=28, spaceAfter=20
    )
    subtitle_style = ParagraphStyle("BookSubtitle", parent=styles["Normal"], alignment=TA_CENTER, fontSize=13)
    text_style = ParagraphStyle(
        "PageText", parent=styles["Normal"], alignment=TA_CENTER, fontSize=14, leading=20, spaceBefore=16
    )
    label_style = ParagraphStyle("MoralLabel", parent=styles["Heading2"], alignment=TA_CENTER)
    moral_style = ParagraphStyle("Moral", parent=styles["Italic"], alignment=TA_CENTER, fontSize=16, leading=22)

    flowables = [
        Spacer(1, 2 * inch),
        Paragraph(data["title"], title_style),
        Spacer(1, 0.3 * inch),
        Paragraph(f"A story about {data['character_name']}", subtitle_style),
        PageBreak(),
    ]

    max_width, max_height = 6.0 * inch, 5.0 * inch
    for page in data["pages"]:
        if not page.get("image_failed") and page.get("image_file"):
            img_path = images_dir / page["image_file"]
            with PILImage.open(img_path) as im:
                w, h = im.size
            scale = min(max_width / w, max_height / h)
            image = RLImage(str(img_path), width=w * scale, height=h * scale)
            image.hAlign = "CENTER"
            flowables.append(image)
        flowables.append(Paragraph(page["page_text"], text_style))
        flowables.append(PageBreak())

    flowables.append(Spacer(1, 2 * inch))
    flowables.append(Paragraph("The moral of the story:", label_style))
    flowables.append(Paragraph(data["moral"], moral_style))

    doc.build(flowables)
    return buf.getvalue()


@app.get("/books/{book_id}/download")
def download_book(book_id: str):
    if not book_id.isalnum():
        raise HTTPException(404, "unknown book_id")
    book_dir = DATA_DIR / book_id
    story_path = book_dir / "story.json"
    if not story_path.exists():
        raise HTTPException(404, "unknown book_id")
    data = json.loads(story_path.read_text())
    pdf_bytes = _build_pdf(data, book_dir / "images")
    safe_title = re.sub(r"[^A-Za-z0-9 _-]", "", data["title"]).strip() or "book"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'},
    )


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Children's Book Generator</title>
<style>
  :root {
    --bg: #fdf6ec;
    --card: #ffffff;
    --ink: #3b2f2f;
    --accent: #e8763c;
    --accent-dark: #c85a25;
    --muted: #8a7f78;
    --border: #ecdfd0;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Segoe UI", Verdana, sans-serif;
    background: var(--bg);
    color: var(--ink);
  }
  header {
    padding: 28px 24px 10px;
    text-align: center;
  }
  header h1 { margin: 0 0 4px; font-size: 1.8rem; color: var(--accent-dark); }
  header p { margin: 0; color: var(--muted); }
  .layout {
    display: flex;
    gap: 24px;
    max-width: 1100px;
    margin: 0 auto;
    padding: 20px 24px 60px;
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  }
  #form-panel { flex: 2; min-width: 340px; }
  #side-panel { flex: 1; min-width: 240px; }
  label { display: block; font-size: 0.85rem; font-weight: 600; margin: 14px 0 4px; }
  .checkbox-label { display: flex; align-items: center; gap: 8px; margin: 16px 0 4px; }
  .checkbox-label input { width: auto; }
  input[type=text], textarea, select, input[type=number] {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.95rem;
    font-family: inherit;
    background: #fffdfb;
  }
  textarea { resize: vertical; min-height: 54px; }
  .row { display: flex; gap: 14px; }
  .row > div { flex: 1; }
  button {
    margin-top: 20px;
    width: 100%;
    padding: 12px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
  }
  button:hover { background: var(--accent-dark); }
  button:disabled { background: var(--muted); cursor: not-allowed; }
  .secondary-btn {
    margin-top: 0;
    width: auto;
    background: transparent;
    color: var(--accent-dark);
    border: 1px solid var(--accent);
    padding: 8px 14px;
    font-size: 0.85rem;
  }
  .secondary-btn:hover { background: var(--bg); color: var(--accent-dark); }
  #progress { margin-top: 16px; font-size: 0.9rem; color: var(--accent-dark); display: none; }
  h3 { margin-top: 0; color: var(--accent-dark); }
  #book-list { list-style: none; padding: 0; margin: 0; }
  #book-list li {
    padding: 8px 10px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    border: 1px solid transparent;
  }
  #book-list li:hover { background: var(--bg); border-color: var(--border); }
  #book-list .meta { color: var(--muted); font-size: 0.78rem; }
  #empty-books { color: var(--muted); font-size: 0.85rem; }

  #viewer { display: none; margin-top: 26px; }
  #viewer .page-frame {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    text-align: center;
  }
  #viewer img { max-width: 100%; max-height: 380px; border-radius: 10px; border: 1px solid var(--border); }
  #viewer .page-text { margin-top: 14px; font-size: 1.05rem; line-height: 1.5; }
  #viewer .nav { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; }
  #viewer .nav button { width: auto; padding: 8px 18px; margin-top: 0; }
  #viewer .counter { color: var(--muted); font-size: 0.85rem; }
  #viewer .book-title { font-size: 1.3rem; color: var(--accent-dark); margin-bottom: 4px; }
  .download-link {
    display: block;
    text-align: center;
    margin-top: 16px;
    color: var(--accent-dark);
    font-weight: 600;
    text-decoration: none;
  }
  .download-link:hover { text-decoration: underline; }
  .moral-page { font-style: italic; }
  .img-failed { padding: 40px 10px; color: var(--muted); border: 1px dashed var(--border); border-radius: 10px; }
</style>
</head>
<body>
<header>
  <h1>Children's Book Generator</h1>
  <p>Describe a character and a moral, get back a short illustrated picture book.</p>
</header>
<div class="layout">
  <div class="panel" id="form-panel">
    <h3>New Book</h3>
    <button type="button" id="randomize-btn" class="secondary-btn">Randomize Inputs</button>
    <form id="book-form">
      <label>Character name</label>
      <input type="text" name="character_name" required placeholder="e.g. Pip">

      <label>Character description</label>
      <textarea name="character_description" required placeholder="e.g. a small orange fox with a blue scarf and round glasses"></textarea>

      <label>Art style</label>
      <input type="text" name="art_style" required placeholder="e.g. soft watercolor storybook">

      <label>Moral of the story</label>
      <input type="text" name="moral" required placeholder="e.g. it's okay to ask for help">

      <div class="row">
        <div>
          <label>Setting / world (optional)</label>
          <input type="text" name="setting" placeholder="e.g. a quiet forest village">
        </div>
        <div>
          <label>Target age range</label>
          <select name="age_range">
            <option value="">Any</option>
            <option value="toddler (2-4)">Toddler (2-4)</option>
            <option value="early reader (5-7)" selected>Early reader (5-7)</option>
            <option value="middle grade (8-10)">Middle grade (8-10)</option>
          </select>
        </div>
      </div>

      <label>Supporting characters (optional)</label>
      <textarea name="supporting_characters" placeholder="e.g. Pip's older sister, a wise old owl"></textarea>

      <div class="row">
        <div>
          <label>Tone / mood</label>
          <select name="tone">
            <option value="">Any</option>
            <option value="silly and playful">Silly and playful</option>
            <option value="gentle and heartwarming" selected>Gentle and heartwarming</option>
            <option value="adventurous">Adventurous</option>
            <option value="spooky-but-safe">Spooky-but-safe</option>
          </select>
        </div>
        <div>
          <label>Number of pages (4-30)</label>
          <input type="number" name="num_pages" min="4" max="30" value="6">
        </div>
      </div>

      <label class="checkbox-label">
        <input type="checkbox" name="rhyming">
        Write the story in rhyme
      </label>

      <button type="submit" id="submit-btn">Generate Book</button>
      <div id="progress"></div>
    </form>
  </div>

  <div class="panel" id="side-panel">
    <h3>Past Books</h3>
    <ul id="book-list"></ul>
    <div id="empty-books">No books yet.</div>
  </div>
</div>

<div class="layout">
  <div id="viewer" style="flex: 1;">
    <div class="page-frame">
      <div class="book-title" id="v-title"></div>
      <div id="v-image-wrap"></div>
      <div class="page-text" id="v-text"></div>
      <div class="nav">
        <button id="v-prev" type="button">&larr; Prev</button>
        <span class="counter" id="v-counter"></span>
        <button id="v-next" type="button">Next &rarr;</button>
      </div>
      <a id="v-download" class="download-link" href="#" download>Download as PDF</a>
    </div>
  </div>
</div>

<script>
let currentBook = null;
let currentPage = 0;

const RANDOM_POOL = {
  character_name: ['Pip', 'Luna', 'Milo', 'Bramble', 'Sage', 'Nimbus', 'Coco', 'Ziggy', 'Clementine', 'Otto'],
  character_description: [
    'a small orange fox with a blue scarf and round glasses',
    'a fluffy white rabbit with oversized ears and a polka-dot bowtie',
    'a curious blue-feathered owl with tiny spectacles',
    'a shy purple dragon with speckled wings',
    'a bold green turtle with a tiny backpack',
    'a sleepy gray koala who wears a knitted hat',
    'a clever red panda with a striped scarf',
    'a tiny yellow duckling with red rain boots',
  ],
  art_style: [
    'soft watercolor storybook',
    'bold flat-color cartoon',
    'pastel pencil sketch',
    'cut-paper collage',
    'whimsical crayon doodle',
    'claymation-style stop-motion look',
    'retro 1960s picture book',
    'dreamy pastel chalk',
  ],
  moral: [
    "it's okay to ask for help",
    'kindness always comes back around',
    'mistakes are how we learn',
    'sharing makes everything better',
    'being different is something to celebrate',
    'slow and steady wins the day',
    'true friends stick together',
    "it's brave to try new things",
  ],
  setting: [
    'a quiet forest village',
    'a floating city in the clouds',
    'an underwater coral kingdom',
    'a cozy treehouse town',
    'a desert oasis full of surprises',
    'a snow-covered mountain village',
    'a bustling city park',
    'a magical library between the shelves',
  ],
  age_range: ['', 'toddler (2-4)', 'early reader (5-7)', 'middle grade (8-10)'],
  supporting_characters: [
    '',
    'a wise old owl',
    'a mischievous younger sibling',
    'a loyal best friend',
    'a grumpy but kind neighbor',
    'a talking compass',
  ],
  tone: ['', 'silly and playful', 'gentle and heartwarming', 'adventurous', 'spooky-but-safe'],
};

function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomizeForm() {
  const form = document.getElementById('book-form');
  form.character_name.value = pickRandom(RANDOM_POOL.character_name);
  form.character_description.value = pickRandom(RANDOM_POOL.character_description);
  form.art_style.value = pickRandom(RANDOM_POOL.art_style);
  form.moral.value = pickRandom(RANDOM_POOL.moral);
  form.setting.value = pickRandom(RANDOM_POOL.setting);
  form.age_range.value = pickRandom(RANDOM_POOL.age_range);
  form.supporting_characters.value = pickRandom(RANDOM_POOL.supporting_characters);
  form.tone.value = pickRandom(RANDOM_POOL.tone);
  form.num_pages.value = 4 + Math.floor(Math.random() * 7); // 4-10
  form.rhyming.checked = Math.random() < 0.5;
}

document.getElementById('randomize-btn').addEventListener('click', randomizeForm);

async function loadBooks() {
  const resp = await fetch('books');
  const books = await resp.json();
  const list = document.getElementById('book-list');
  const empty = document.getElementById('empty-books');
  list.innerHTML = '';
  if (books.length === 0) { empty.style.display = 'block'; return; }
  empty.style.display = 'none';
  for (const b of books) {
    const li = document.createElement('li');
    li.innerHTML = `${b.title}<div class="meta">${b.character_name} · ${b.num_pages} pages · ${b.created_at}</div>`;
    li.onclick = () => openBook(b.book_id);
    list.appendChild(li);
  }
}

async function openBook(bookId) {
  const resp = await fetch('books/' + bookId);
  if (!resp.ok) { alert('Could not load that book.'); return; }
  const data = await resp.json();
  showViewer(data);
}

function showViewer(book) {
  currentBook = book;
  currentPage = 0;
  document.getElementById('viewer').style.display = 'block';
  document.getElementById('v-title').textContent = book.title;
  document.getElementById('v-download').href = 'books/' + book.book_id + '/download';
  renderPage();
}

function renderPage() {
  const totalPages = currentBook.pages.length + 1; // +1 for the moral page
  const wrap = document.getElementById('v-image-wrap');
  const text = document.getElementById('v-text');
  const counter = document.getElementById('v-counter');

  if (currentPage < currentBook.pages.length) {
    const page = currentBook.pages[currentPage];
    if (page.image_failed || !page.image_file) {
      wrap.innerHTML = '<div class="img-failed">Illustration could not be generated for this page.</div>';
    } else {
      wrap.innerHTML = `<img src="books/${currentBook.book_id}/images/${page.image_file}">`;
    }
    text.textContent = page.page_text;
    text.classList.remove('moral-page');
  } else {
    wrap.innerHTML = '';
    text.textContent = 'The moral of the story: ' + currentBook.moral;
    text.classList.add('moral-page');
  }
  counter.textContent = `Page ${currentPage + 1} of ${totalPages}`;
  document.getElementById('v-prev').disabled = currentPage === 0;
  document.getElementById('v-next').disabled = currentPage === totalPages - 1;
}

document.getElementById('v-prev').onclick = () => { if (currentPage > 0) { currentPage--; renderPage(); } };
document.getElementById('v-next').onclick = () => {
  if (currentPage < currentBook.pages.length) { currentPage++; renderPage(); }
};

document.getElementById('book-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const payload = {
    character_name: form.character_name.value,
    character_description: form.character_description.value,
    art_style: form.art_style.value,
    moral: form.moral.value,
    setting: form.setting.value,
    age_range: form.age_range.value,
    supporting_characters: form.supporting_characters.value,
    tone: form.tone.value,
    num_pages: parseInt(form.num_pages.value, 10),
    rhyming: form.rhyming.checked,
  };

  const submitBtn = document.getElementById('submit-btn');
  const progress = document.getElementById('progress');
  submitBtn.disabled = true;
  progress.style.display = 'block';
  progress.textContent = 'Submitting...';

  const resp = await fetch('generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    progress.textContent = 'Something went wrong submitting the request.';
    submitBtn.disabled = false;
    return;
  }
  const { job_id } = await resp.json();

  const poll = setInterval(async () => {
    const statusResp = await fetch('status/' + job_id);
    const job = await statusResp.json();
    progress.textContent = job.progress || job.status;
    if (job.status === 'done') {
      clearInterval(poll);
      submitBtn.disabled = false;
      progress.style.display = 'none';
      showViewer(job.result);
      loadBooks();
    } else if (job.status === 'error') {
      clearInterval(poll);
      submitBtn.disabled = false;
      progress.textContent = 'Error: ' + job.progress;
    }
  }, 1500);
});

loadBooks();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE
