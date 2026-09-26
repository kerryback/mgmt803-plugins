from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>World 1-1</title>
<style>
  html, body {
    margin: 0; padding: 0; height: 100%;
    background: #000;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Courier New', monospace;
    color: #fff;
    overflow: hidden;
  }
  #wrap { position: relative; }
  canvas {
    background: #5c94fc;
    display: block;
    image-rendering: pixelated;
  }
  #hud {
    position: absolute; top: -30px; left: 0; right: 0;
    display: flex; justify-content: space-between;
    font-size: 15px; font-weight: bold;
    color: #fff; letter-spacing: 1px;
  }
  #overlay {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    display: none;
    align-items: center; justify-content: center; flex-direction: column;
    background: rgba(0, 0, 0, 0.75);
    text-align: center;
  }
  #overlay h1 { font-size: 32px; margin: 0 0 8px 0; color: #fbd000; }
  #overlay p { margin: 4px 0; font-size: 16px; }
  #overlay button {
    margin-top: 14px; padding: 8px 18px; font-size: 16px;
    border: none; border-radius: 4px; cursor: pointer;
    background: #fbd000; font-weight: bold;
  }
  #help {
    position: absolute; bottom: -26px; left: 0; right: 0;
    text-align: center;
    font-size: 12px; color: #cfd8e3;
  }
</style>
</head>
<body>
<div id="wrap">
  <div id="hud">
    <span id="score">MARIO 000000</span>
    <span id="coins">&#127775; x00</span>
    <span id="world">WORLD 1-1</span>
    <span id="time">TIME 400</span>
    <span id="lives">x3</span>
  </div>
  <canvas id="game" width="640" height="480"></canvas>
  <div id="help">Arrow keys / A,D to move &middot; Shift to run &middot; Space / Up / W to jump</div>
  <div id="overlay">
    <h1 id="overlayTitle">Game Over</h1>
    <p id="overlayMsg"></p>
    <button id="restartBtn">Play Again</button>
  </div>
</div>
<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const W = canvas.width, H = canvas.height;
const TILE = 32;
const COLS_VIEW = W / TILE;
const ROWS = H / TILE; // 15
const GROUND_TOP_ROW = 13; // rows 13,14 are normal ground surface

const scoreEl = document.getElementById("score");
const coinsEl = document.getElementById("coins");
const timeEl = document.getElementById("time");
const livesEl = document.getElementById("lives");
const overlay = document.getElementById("overlay");
const overlayTitle = document.getElementById("overlayTitle");
const overlayMsg = document.getElementById("overlayMsg");
document.getElementById("restartBtn").addEventListener("click", () => {
  if (lives <= 0) { score = 0; lives = 3; }
  startLevel();
});

// ---------- Level construction ----------
let TOTAL_COLS;
let grid; // grid[row][col] -> tile char
let pipeTops; // set of "row,col" that are pipe top-left (for lip rendering)
let pipeLeftCols; // set of "row,col" that are the left column of a pipe pair
let mushroomBlocks; // set of "row,col" that give a mushroom instead of coin
let flagCol, castleStart;

function addGroundRange(colStart, colEnd) {
  for (let c = colStart; c <= colEnd; c++) {
    grid[13][c] = 'G';
    grid[14][c] = 'G';
  }
}

function addPipe(col, heightTiles) {
  const topRow = 13 - heightTiles + 1;
  for (let r = topRow; r <= 14; r++) {
    grid[r][col] = 'p';
    grid[r][col + 1] = 'p';
    pipeLeftCols.add(r + ',' + col);
  }
  pipeTops.add(topRow + ',' + col);
}

function addBlockRow(row, colStart, pattern, mushroomAt) {
  // pattern: string of 'B' or '?' chars
  for (let i = 0; i < pattern.length; i++) {
    const col = colStart + i;
    grid[row][col] = pattern[i];
    if (pattern[i] === '?' && mushroomAt && mushroomAt.includes(col)) {
      mushroomBlocks.add(row + ',' + col);
    }
  }
}

function buildLevel() {
  TOTAL_COLS = 182;
  grid = [];
  for (let r = 0; r < ROWS; r++) grid.push(new Array(TOTAL_COLS).fill('.'));
  pipeTops = new Set();
  pipeLeftCols = new Set();
  mushroomBlocks = new Set();

  // Section A: 0-59
  addGroundRange(0, 59);
  addBlockRow(9, 16, "?B?B");
  grid[5][20] = '?';
  addPipe(28, 2);
  addPipe(35, 3);
  addPipe(45, 4);
  addBlockRow(9, 50, "B?BB", [51]);

  // Pit
  // 60-61 empty

  // Section B: 62-83
  addGroundRange(62, 83);
  addBlockRow(9, 70, "B??B");
  addPipe(78, 2);

  // Pit
  // 84-85 empty

  // Section C: 86-149
  addGroundRange(86, 149);
  addBlockRow(9, 95, "BB?BB", [97]);
  addPipe(103, 3);
  addPipe(112, 4);
  addBlockRow(9, 130, "?BB?");
  addPipe(138, 2);

  // Staircase up: 150-157, height 1..8
  for (let i = 0; i < 8; i++) {
    const col = 150 + i;
    const h = i + 1;
    const topRow = 14 - h;
    for (let r = topRow; r <= 14; r++) grid[r][col] = 'G';
  }
  // Plateau
  for (let c = 158; c <= 159; c++) {
    for (let r = 6; r <= 14; r++) grid[r][c] = 'G';
  }
  // Gap at 160 (drop off plateau), ground resumes at 161
  addGroundRange(161, 181);

  flagCol = 168;
  castleStart = 174;

  return {
    goombas: [
      { col: 25 }, { col: 40 }, { col: 42 }, { col: 57 },
      { col: 65 }, { col: 81 },
      { col: 90 }, { col: 92 }, { col: 108 },
      { col: 120 }, { col: 122 }, { col: 124 }, { col: 143 },
    ],
  };
}

function isSolid(ch) {
  return ch === 'G' || ch === 'B' || ch === '?' || ch === 'U' || ch === 'p';
}

// ---------- Game state ----------
let mario, entities, mushrooms, particles, coinPops;
let cameraX, score, coins, timeLeft, lives, running, gameOver;
let timeAcc;
const GRAVITY = 2000;
const MOVE_ACCEL = 900;
const MOVE_MAX = 220;
const RUN_MAX = 340;
const FRICTION = 1200;
const JUMP_V = -680;
const STOMP_BOUNCE = -420;
const keys = {};

function startLevel() {
  const built = buildLevel();
  mario = {
    x: 2 * TILE, y: 10 * TILE, w: TILE * 0.7, h: TILE * 0.9,
    vx: 0, vy: 0, onGround: false, facing: 1, big: false,
    invincible: 0, dead: false, winSlide: false,
  };
  entities = built.goombas.map(g => ({
    type: 'goomba', col: g.col,
    x: g.col * TILE, y: GROUND_TOP_ROW * TILE - TILE,
    w: TILE * 0.85, h: TILE * 0.85,
    vx: -60, alive: true, squished: 0,
  }));
  mushrooms = [];
  particles = [];
  coinPops = [];
  cameraX = 0;
  timeLeft = 400;
  timeAcc = 0;
  running = true;
  gameOver = false;
  overlay.style.display = "none";
  updateHud();
  lastTime = null;
  requestAnimationFrame(loop);
}

function fullRestart() {
  score = 0; coins = 0; lives = 3;
  startLevel();
}

function updateHud() {
  scoreEl.textContent = "MARIO " + String(score).padStart(6, '0');
  coinsEl.textContent = "⭐ x" + String(coins).padStart(2, '0');
  timeEl.textContent = "TIME " + Math.max(0, Math.ceil(timeLeft));
  livesEl.textContent = "x" + Math.max(0, lives);
}

function tileAt(row, col) {
  if (row < 0 || row >= ROWS || col < 0 || col >= TOTAL_COLS) return '.';
  return grid[row][col];
}

function rectVsTiles(x, y, w, h) {
  // returns list of {row, col, ch}
  // far edges use an exclusive bound so a rect exactly flush against a tile
  // boundary (e.g. standing on the ground) doesn't register that tile as a
  // collision on the perpendicular axis.
  const results = [];
  const c0 = Math.floor(x / TILE), c1 = Math.floor((x + w - 0.01) / TILE);
  const r0 = Math.floor(y / TILE), r1 = Math.floor((y + h - 0.01) / TILE);
  for (let r = r0; r <= r1; r++) {
    for (let c = c0; c <= c1; c++) {
      const ch = tileAt(r, c);
      if (isSolid(ch)) results.push({ row: r, col: c, ch });
    }
  }
  return results;
}

function hitBlockFromBelow(row, col) {
  const ch = grid[row][col];
  if (ch === '?') {
    grid[row][col] = 'U';
    const key = row + ',' + col;
    if (mushroomBlocks.has(key)) {
      mushrooms.push({
        x: col * TILE, y: row * TILE - TILE, w: TILE * 0.8, h: TILE * 0.8,
        vx: 60, vy: 0, emerging: 20,
      });
    } else {
      coins++;
      score += 200;
      coinPops.push({ x: col * TILE + TILE / 2, y: row * TILE, life: 20 });
    }
    updateHud();
  } else if (ch === 'B') {
    if (mario.big) {
      grid[row][col] = '.';
      score += 50;
      for (let i = 0; i < 4; i++) {
        particles.push({
          x: col * TILE + TILE / 2, y: row * TILE + TILE / 2,
          vx: (Math.random() - 0.5) * 300, vy: -Math.random() * 300 - 100,
          life: 40,
        });
      }
      updateHud();
    } else {
      bumpTiles.push({ row, col, t: 0 });
    }
  }
}

let bumpTiles = [];

function killMario() {
  if (mario.invincible > 0 || mario.dead) return;
  if (mario.big) {
    mario.big = false;
    mario.h = TILE * 0.9;
    mario.invincible = 2;
  } else {
    mario.dead = true;
    running = false;
    lives--;
    updateHud();
    setTimeout(() => {
      if (lives <= 0) {
        gameOver = true;
        overlayTitle.textContent = "Game Over";
        overlayMsg.textContent = "Final Score: " + score;
        overlay.style.display = "flex";
      } else {
        startLevel();
      }
    }, 900);
  }
}

function update(dt) {
  if (!running) return;

  if (!mario.winSlide) {
    timeAcc += dt;
    if (timeAcc >= 1) {
      timeAcc -= 1;
      timeLeft -= 1;
      updateHud();
      if (timeLeft <= 0) { killMario(); return; }
    }
  }

  if (mario.invincible > 0) mario.invincible -= dt;

  if (mario.winSlide) {
    // slide down pole then walk to castle
    if (mario.y < (GROUND_TOP_ROW - 1) * TILE) {
      mario.y += 200 * dt;
    } else {
      mario.x += 90 * dt;
      if (mario.x > (castleStart + 3) * TILE) {
        running = false;
        overlayTitle.textContent = "Course Clear!";
        overlayMsg.textContent = "Score: " + score + "   Time Bonus: " + Math.ceil(timeLeft) * 10;
        score += Math.ceil(timeLeft) * 10;
        updateHud();
        overlay.style.display = "flex";
      }
    }
  } else {
    // --- horizontal input ---
    const left = keys["ArrowLeft"] || keys["a"] || keys["A"];
    const right = keys["ArrowRight"] || keys["d"] || keys["D"];
    const run = keys["Shift"];
    const maxSpeed = run ? RUN_MAX : MOVE_MAX;

    if (left && !right) {
      mario.vx -= MOVE_ACCEL * dt;
      mario.facing = -1;
    } else if (right && !left) {
      mario.vx += MOVE_ACCEL * dt;
      mario.facing = 1;
    } else {
      const f = FRICTION * dt;
      if (mario.vx > 0) mario.vx = Math.max(0, mario.vx - f);
      else if (mario.vx < 0) mario.vx = Math.min(0, mario.vx + f);
    }
    mario.vx = Math.max(-maxSpeed, Math.min(maxSpeed, mario.vx));

    // jump
    const jumpPressed = keys[" "] || keys["ArrowUp"] || keys["w"] || keys["W"];
    if (jumpPressed && mario.onGround) {
      mario.vy = JUMP_V;
      mario.onGround = false;
    }

    mario.vy += GRAVITY * dt;
    if (mario.vy > 1000) mario.vy = 1000;

    // move X, resolve
    mario.x += mario.vx * dt;
    mario.x = Math.max(cameraX, mario.x);
    let hits = rectVsTiles(mario.x, mario.y, mario.w, mario.h);
    for (const h of hits) {
      if (mario.vx > 0) mario.x = h.col * TILE - mario.w;
      else if (mario.vx < 0) mario.x = (h.col + 1) * TILE;
      mario.vx = 0;
    }

    // move Y, resolve
    mario.y += mario.vy * dt;
    mario.onGround = false;
    hits = rectVsTiles(mario.x, mario.y, mario.w, mario.h);
    for (const h of hits) {
      if (mario.vy > 0) {
        mario.y = h.row * TILE - mario.h;
        mario.vy = 0;
        mario.onGround = true;
      } else if (mario.vy < 0) {
        mario.y = (h.row + 1) * TILE;
        mario.vy = 0;
        hitBlockFromBelow(h.row, h.col);
      }
    }

    // fell into a pit
    if (mario.y > H + 100) {
      killMario();
      return;
    }

    // flagpole
    if (!mario.winSlide && mario.x + mario.w >= flagCol * TILE) {
      const touchRow = Math.floor(mario.y / TILE);
      const bonus = Math.max(0, (GROUND_TOP_ROW - touchRow)) * 100;
      score += bonus + 100;
      mario.x = flagCol * TILE;
      mario.winSlide = true;
      mario.vx = 0; mario.vy = 0;
      updateHud();
    }
  }

  // camera only advances forward
  const desired = mario.x - W * 0.35;
  cameraX = Math.max(cameraX, Math.min(desired, TOTAL_COLS * TILE - W));
  cameraX = Math.max(0, cameraX);

  // --- goombas ---
  for (const e of entities) {
    if (!e.alive) continue;
    if (e.squished > 0) {
      e.squished -= dt;
      if (e.squished <= 0) e.alive = false;
      continue;
    }
    e.vy = (e.vy || 0) + GRAVITY * dt;
    e.x += e.vx * dt;
    let eh = rectVsTiles(e.x, e.y, e.w, e.h);
    for (const h of eh) {
      if (e.vx > 0) e.x = h.col * TILE - e.w;
      else e.x = (h.col + 1) * TILE;
      e.vx *= -1;
    }
    e.y += e.vy * dt;
    eh = rectVsTiles(e.x, e.y, e.w, e.h);
    for (const h of eh) {
      if (e.vy > 0) { e.y = h.row * TILE - e.h; e.vy = 0; }
    }
    if (e.y > H + 200) { e.alive = false; continue; }

    // collision with mario
    if (!mario.winSlide && mario.invincible <= 0 &&
        mario.x < e.x + e.w && mario.x + mario.w > e.x &&
        mario.y < e.y + e.h && mario.y + mario.h > e.y) {
      const marioBottom = mario.y + mario.h;
      if (mario.vy > 0 && marioBottom - e.y < e.h * 0.6) {
        e.squished = 0.3;
        e.vx = 0;
        mario.vy = STOMP_BOUNCE;
        score += 100;
        updateHud();
      } else {
        killMario();
      }
    }
  }

  // --- mushrooms ---
  for (const m of mushrooms) {
    if (m.emerging > 0) {
      m.emerging--;
      m.y -= 1;
      continue;
    }
    m.vy += GRAVITY * dt;
    m.x += m.vx * dt;
    let mh = rectVsTiles(m.x, m.y, m.w, m.h);
    for (const h of mh) {
      if (m.vx > 0) m.x = h.col * TILE - m.w; else m.x = (h.col + 1) * TILE;
      m.vx *= -1;
    }
    m.y += m.vy * dt;
    mh = rectVsTiles(m.x, m.y, m.w, m.h);
    for (const h of mh) {
      if (m.vy > 0) { m.y = h.row * TILE - m.h; m.vy = 0; }
    }
    if (!m.taken && mario.x < m.x + m.w && mario.x + mario.w > m.x &&
        mario.y < m.y + m.h && mario.y + mario.h > m.y) {
      m.taken = true;
      if (!mario.big) {
        mario.big = true;
        mario.h = TILE * 1.5;
      }
      score += 1000;
      updateHud();
    }
  }
  mushrooms = mushrooms.filter(m => !m.taken && m.y < H + 200);

  for (const b of bumpTiles) b.t += dt;
  bumpTiles = bumpTiles.filter(b => b.t < 0.15);

  for (const p of particles) { p.x += p.vx * dt; p.y += p.vy * dt; p.vy += GRAVITY * dt * 0.5; p.life--; }
  particles = particles.filter(p => p.life > 0);
  for (const c of coinPops) { c.y -= 60 * dt; c.life--; }
  coinPops = coinPops.filter(c => c.life > 0);
}

// ---------- Drawing ----------
function drawTile(ch, px, py, isTop) {
  switch (ch) {
    case 'G':
      ctx.fillStyle = '#c84c0c';
      ctx.fillRect(px, py, TILE, TILE);
      ctx.fillStyle = '#e07830';
      ctx.fillRect(px, py, TILE, 6);
      ctx.strokeStyle = 'rgba(0,0,0,0.25)';
      ctx.strokeRect(px + 1, py + 1, TILE - 2, TILE - 2);
      break;
    case 'B':
      ctx.fillStyle = '#c84c0c';
      ctx.fillRect(px, py, TILE, TILE);
      ctx.strokeStyle = 'rgba(0,0,0,0.35)';
      ctx.lineWidth = 2;
      ctx.strokeRect(px + 2, py + 2, TILE - 4, TILE - 4);
      ctx.beginPath();
      ctx.moveTo(px + TILE / 2, py + 2); ctx.lineTo(px + TILE / 2, py + TILE - 2);
      ctx.stroke();
      break;
    case '?':
      ctx.fillStyle = '#fbd000';
      ctx.fillRect(px, py, TILE, TILE);
      ctx.strokeStyle = '#8a5a00';
      ctx.lineWidth = 2;
      ctx.strokeRect(px + 2, py + 2, TILE - 4, TILE - 4);
      ctx.fillStyle = '#8a5a00';
      ctx.font = 'bold 18px monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('?', px + TILE / 2, py + TILE / 2 + 1);
      break;
    case 'U':
      ctx.fillStyle = '#9c7a4a';
      ctx.fillRect(px, py, TILE, TILE);
      ctx.strokeStyle = 'rgba(0,0,0,0.3)';
      ctx.strokeRect(px + 1, py + 1, TILE - 2, TILE - 2);
      break;
    case 'p':
      ctx.fillStyle = '#1f9e2c';
      ctx.fillRect(px, py, TILE * 2, TILE);
      ctx.strokeStyle = '#0d5f18';
      ctx.lineWidth = 2;
      ctx.strokeRect(px + 1, py + 1, TILE * 2 - 2, TILE - 2);
      if (isTop) {
        ctx.fillStyle = '#26b838';
        ctx.fillRect(px - 4, py, TILE * 2 + 8, 12);
        ctx.strokeRect(px - 3, py + 1, TILE * 2 + 6, 10);
      }
      break;
  }
}

function drawBackground() {
  ctx.fillStyle = '#5c94fc';
  ctx.fillRect(0, 0, W, H);
  // clouds & bushes, parallax
  ctx.fillStyle = '#ffffff';
  for (let i = 0; i < 40; i++) {
    const bx = i * 300 - (cameraX * 0.3) % 300;
    drawCloud(bx + 50, 60 + (i % 3) * 20);
  }
  ctx.fillStyle = '#1f9e2c';
  for (let i = 0; i < 60; i++) {
    const bx = i * 260 - (cameraX * 0.6) % 260;
    drawBush(bx + 120, GROUND_TOP_ROW * TILE);
  }
}

function drawCloud(x, y) {
  ctx.beginPath();
  ctx.arc(x, y, 14, 0, Math.PI * 2);
  ctx.arc(x + 16, y - 6, 16, 0, Math.PI * 2);
  ctx.arc(x + 32, y, 14, 0, Math.PI * 2);
  ctx.fill();
}
function drawBush(x, y) {
  ctx.beginPath();
  ctx.arc(x, y, 12, 0, Math.PI * 2);
  ctx.arc(x + 14, y - 6, 14, 0, Math.PI * 2);
  ctx.arc(x + 28, y, 12, 0, Math.PI * 2);
  ctx.fill();
}

function drawMario() {
  ctx.save();
  ctx.translate(mario.x + mario.w / 2 - cameraX, mario.y + mario.h / 2);
  if (mario.facing < 0) ctx.scale(-1, 1);
  const flashing = mario.invincible > 0 && Math.floor(mario.invincible * 12) % 2 === 0;
  if (!flashing) {
    const hatColor = '#e21818';
    const skinColor = '#f2b48c';
    const overallColor = mario.big ? '#1a5fd6' : '#1a5fd6';
    const hh = mario.h;
    // legs/overalls
    ctx.fillStyle = overallColor;
    ctx.fillRect(-mario.w / 2, -2, mario.w, hh / 2);
    // torso/shirt
    ctx.fillStyle = hatColor;
    ctx.fillRect(-mario.w / 2, -hh / 2 + 6, mario.w, hh / 3);
    // head
    ctx.fillStyle = skinColor;
    ctx.fillRect(-mario.w / 2 + 3, -hh / 2 - 4, mario.w - 6, 12);
    // hat
    ctx.fillStyle = hatColor;
    ctx.fillRect(-mario.w / 2 + 1, -hh / 2 - 8, mario.w - 2, 6);
    ctx.fillRect(2, -hh / 2 - 4, mario.w / 2, 4);
  }
  ctx.restore();
}

function drawGoomba(e) {
  ctx.save();
  const px = e.x - cameraX;
  if (e.squished > 0) {
    ctx.fillStyle = '#8a4b2a';
    ctx.fillRect(px, e.y + e.h * 0.7, e.w, e.h * 0.3);
  } else {
    ctx.fillStyle = '#8a4b2a';
    ctx.beginPath();
    ctx.ellipse(px + e.w / 2, e.y + e.h / 2, e.w / 2, e.h / 2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#5a2f18';
    ctx.fillRect(px + 2, e.y + e.h - 8, e.w / 2 - 4, 8);
    ctx.fillRect(px + e.w / 2 + 2, e.y + e.h - 8, e.w / 2 - 4, 8);
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(px + e.w * 0.35, e.y + e.h * 0.4, 4, 0, Math.PI * 2);
    ctx.arc(px + e.w * 0.65, e.y + e.h * 0.4, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(px + e.w * 0.35, e.y + e.h * 0.4, 2, 0, Math.PI * 2);
    ctx.arc(px + e.w * 0.65, e.y + e.h * 0.4, 2, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawMushroom(m) {
  const px = m.x - cameraX;
  ctx.fillStyle = '#e21818';
  ctx.beginPath();
  ctx.arc(px + m.w / 2, m.y + m.h * 0.4, m.w / 2, Math.PI, 0);
  ctx.fill();
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  ctx.arc(px + m.w * 0.3, m.y + m.h * 0.3, 4, 0, Math.PI * 2);
  ctx.arc(px + m.w * 0.7, m.y + m.h * 0.3, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#f2c49b';
  ctx.fillRect(px + m.w * 0.2, m.y + m.h * 0.4, m.w * 0.6, m.h * 0.5);
}

function drawFlagAndCastle() {
  const px = flagCol * TILE - cameraX;
  ctx.strokeStyle = '#cfcfcf';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(px + TILE / 2, 6 * TILE);
  ctx.lineTo(px + TILE / 2, 14 * TILE);
  ctx.stroke();
  ctx.fillStyle = '#2ecc40';
  const flagY = mario.winSlide ? Math.min(mario.y + mario.h / 2, 13 * TILE) : 6 * TILE + 4;
  ctx.beginPath();
  ctx.moveTo(px + TILE / 2, flagY);
  ctx.lineTo(px + TILE / 2 + 20, flagY + 8);
  ctx.lineTo(px + TILE / 2, flagY + 16);
  ctx.closePath();
  ctx.fill();

  const cx = castleStart * TILE - cameraX;
  ctx.fillStyle = '#a8a8a8';
  ctx.fillRect(cx, 9 * TILE, TILE * 6, 5 * TILE);
  ctx.fillStyle = '#8c8c8c';
  for (let i = 0; i < 4; i++) ctx.fillRect(cx + i * TILE * 2, 8 * TILE, TILE, TILE);
  ctx.fillStyle = '#3a3a3a';
  ctx.fillRect(cx + TILE * 2.5, 11 * TILE, TILE, TILE * 3);
}

function draw() {
  drawBackground();

  const c0 = Math.max(0, Math.floor(cameraX / TILE) - 1);
  const c1 = Math.min(TOTAL_COLS - 1, c0 + COLS_VIEW + 2);
  for (let r = 0; r < ROWS; r++) {
    for (let c = c0; c <= c1; c++) {
      const ch = grid[r][c];
      if (ch === '.') continue;
      if (ch === 'p' && !pipeLeftCols.has(r + ',' + c)) continue; // right column drawn with the left one
      let py = r * TILE;
      const bump = bumpTiles.find(b => b.row === r && b.col === c);
      if (bump) py -= Math.sin((0.15 - bump.t) / 0.15 * Math.PI) * 6;
      if (ch === 'p') {
        const isTop = pipeTops.has(r + ',' + c);
        drawTile('p', c * TILE - cameraX, py, isTop);
      } else {
        drawTile(ch, c * TILE - cameraX, py);
      }
    }
  }
  drawFlagAndCastle();

  for (const e of entities) if (e.alive) drawGoomba(e);
  for (const m of mushrooms) drawMushroom(m);
  drawMario();

  ctx.fillStyle = '#8a5a00';
  ctx.font = 'bold 16px monospace';
  ctx.textAlign = 'center';
  for (const c of coinPops) {
    ctx.globalAlpha = Math.max(0, c.life / 20);
    ctx.fillText('+200', c.x - cameraX, c.y);
  }
  ctx.globalAlpha = 1;

  ctx.fillStyle = '#a0522d';
  for (const p of particles) {
    ctx.fillRect(p.x - cameraX, p.y, 4, 4);
  }
}

let lastTime = null;
function loop(t) {
  if (lastTime === null) lastTime = t;
  const dt = Math.min(0.033, (t - lastTime) / 1000);
  lastTime = t;
  update(dt);
  draw();
  if (running) requestAnimationFrame(loop);
  else lastTime = null;
}

window.addEventListener("keydown", (e) => {
  keys[e.key] = true;
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", " "].includes(e.key)) e.preventDefault();
});
window.addEventListener("keyup", (e) => { keys[e.key] = false; });

fullRestart();
</script>
</body>
</html>
"""
