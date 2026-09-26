"""Build shareable versions of Lizard Leap from game.py.

    python build.py html   ->  dist/LizardLeap.html + docs/index.html  (plays in any browser, no Python needed)
    python build.py exe    ->  dist/LizardLeap.exe   (Windows app with the FastAPI server inside)
    python build.py        ->  both

game.py stays the one source to edit; re-run this after changing it.
The exe target needs PyInstaller (python -m pip install pyinstaller) and Pillow for the icon.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
DIST = HERE / "dist"
# PyInstaller's scratch files live outside the project: OneDrive locks files it's syncing,
# which makes PyInstaller's cleanup fail with "Access is denied".
WORK = Path(tempfile.gettempdir()) / "LizardLeap-build"


def build_html():
    from game import PAGE

    server_line = 'const SCORE_API = "/api/highscore";'
    if server_line not in PAGE:
        sys.exit(f"build.py: couldn't find `{server_line}` in game.py - did it get renamed?")
    page = PAGE.replace(server_line, 'const SCORE_API = "";   // standalone: best score saved in the browser')

    # dist/LizardLeap.html is the file to send people; docs/index.html is what GitHub Pages serves.
    for out in (DIST / "LizardLeap.html", HERE / "docs" / "index.html"):
        out.parent.mkdir(exist_ok=True)
        out.write_text(page, encoding="utf-8")
        print(f"Built {out.relative_to(HERE)} ({out.stat().st_size // 1024} KB)")


# The standing lizard from game.py, drawn on a little patch of desert for the app icon.
ICON_SPRITE = [
    "...........GGG..",
    "..........GGGGEG",
    "....GDGDGDGGGGGG",
    "..GGGGGGGGGGGG..",
    "GG.LLLLLLLLL....",
    "....G.....G.....",
    "...G.......G....",
]
ICON_COLORS = {"G": "#5dae3c", "D": "#35751f", "L": "#cfe57e", "E": "#161616"}


def make_icon() -> Path:
    from PIL import Image, ImageColor, ImageDraw

    grid = 20                                   # icon is 20x20 sprite pixels
    img = Image.new("RGBA", (grid, grid), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, grid - 1, 13], fill="#7cc4e8")             # sky
    d.rectangle([0, 14, grid - 1, grid - 1], fill="#e8b877")      # sand
    mask = Image.new("L", (grid, grid), 0)                         # trim to a rounded square
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, grid - 1, grid - 1], radius=4, fill=255)
    img.putalpha(mask)
    d.rounded_rectangle([0, 0, grid - 1, grid - 1], radius=4, outline="#2b2118")
    top, left = 14 - len(ICON_SPRITE), 2
    for r, row in enumerate(ICON_SPRITE):
        for c, ch in enumerate(row):
            if ch != ".":
                img.putpixel((left + c, top + r), ImageColor.getrgb(ICON_COLORS[ch]))

    WORK.mkdir(exist_ok=True)
    out = WORK / "icon.ico"
    img.resize((256, 256), Image.NEAREST).save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return out


def build_exe():
    icon = make_icon()
    cmd = [
        sys.executable, "-m", "PyInstaller", str(HERE / "game.py"),
        "--name", "LizardLeap",
        "--onefile",                         # a single .exe to hand to people
        "--icon", str(icon.resolve()),
        "--collect-submodules", "uvicorn",   # uvicorn loads parts of itself by name at runtime
        "--distpath", str(DIST),
        "--workpath", str(WORK / "pyinstaller"),
        "--specpath", str(WORK),
        "--noconfirm", "--clean", "--log-level", "WARN",
    ]
    print("Building LizardLeap.exe (takes a minute)...")
    subprocess.run(cmd, check=True, cwd=HERE)
    out = DIST / "LizardLeap.exe"
    print(f"Built {out.relative_to(HERE)} ({out.stat().st_size // (1024 * 1024)} MB)")


TARGETS = {"html": build_html, "exe": build_exe}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(TARGETS)
    for name in wanted:
        if name not in TARGETS:
            sys.exit(f"Unknown target '{name}'. Choose from: {', '.join(TARGETS)}")
        TARGETS[name]()
