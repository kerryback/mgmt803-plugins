from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Sammy the Owl</title>
<style>
    * { box-sizing: border-box; }
    body {
        margin: 0;
        min-height: 100vh;
        font-family: 'Segoe UI', sans-serif;
        background: #00205b;
        color: #fff;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 16px;
    }
    h1 { margin: 0 0 12px; font-size: 1.5rem; color: #c1c6c8; }
    .subtitle { color: #8fa3c4; font-size: 0.85rem; margin-bottom: 10px; }
    canvas {
        background: #70c5ce;
        border-radius: 10px;
        border: 3px solid #c1c6c8;
        box-shadow: 0 20px 45px rgba(0,0,0,0.5);
        touch-action: none;
        cursor: pointer;
        max-width: 100%;
        height: auto;
    }
</style>
</head>
<body>
    <h1>&#128038; Sammy the Owl</h1>
    <div class="subtitle">Rice University's own &mdash; click / tap / press Space to flap</div>
    <canvas id="game" width="400" height="600"></canvas>

<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height;
const GROUND_H = 80;

const GRAVITY = 0.45;
const FLAP = -8;
const PIPE_W = 62;
const PIPE_GAP = 155;
const PIPE_SPEED = 2.6;
const PIPE_SPACING = 210;

let bird, pipes, score, best, state, groundOffset, frame;

function resetGame() {
    bird = { x: 90, y: H / 2, vy: 0, r: 14 };
    pipes = [];
    score = 0;
    groundOffset = 0;
    frame = 0;
    state = 'ready';
}

best = parseInt(localStorage.getItem('flappyBest') || '0', 10);
resetGame();

function spawnPipe() {
    const margin = 60;
    const gapY = margin + Math.random() * (H - GROUND_H - margin * 2 - PIPE_GAP);
    pipes.push({ x: W + PIPE_W, gapY, passed: false });
}

function flap() {
    if (state === 'ready') {
        state = 'playing';
        bird.vy = FLAP;
    } else if (state === 'playing') {
        bird.vy = FLAP;
    } else if (state === 'gameover') {
        resetGame();
    }
}

canvas.addEventListener('mousedown', flap);
canvas.addEventListener('touchstart', (e) => { e.preventDefault(); flap(); }, { passive: false });
window.addEventListener('keydown', (e) => {
    if (e.code === 'Space') { e.preventDefault(); flap(); }
});

function update() {
    groundOffset = (groundOffset + PIPE_SPEED) % 24;

    if (state !== 'playing') return;

    frame++;
    bird.vy += GRAVITY;
    bird.y += bird.vy;

    if (frame % Math.round(PIPE_SPACING / PIPE_SPEED) === 0) spawnPipe();

    pipes.forEach(p => p.x -= PIPE_SPEED);
    while (pipes.length && pipes[0].x < -PIPE_W) pipes.shift();

    pipes.forEach(p => {
        if (!p.passed && p.x + PIPE_W < bird.x) {
            p.passed = true;
            score++;
        }
    });

    // collisions
    if (bird.y + bird.r > H - GROUND_H || bird.y - bird.r < 0) {
        endGame();
    }
    pipes.forEach(p => {
        const inX = bird.x + bird.r > p.x && bird.x - bird.r < p.x + PIPE_W;
        const inGap = bird.y - bird.r > p.gapY && bird.y + bird.r < p.gapY + PIPE_GAP;
        if (inX && !inGap) endGame();
    });
}

function endGame() {
    if (state !== 'playing') return;
    state = 'gameover';
    if (score > best) {
        best = score;
        localStorage.setItem('flappyBest', best);
    }
}

function drawBackground() {
    const sky = ctx.createLinearGradient(0, 0, 0, H - GROUND_H);
    sky.addColorStop(0, '#4ec0e9');
    sky.addColorStop(1, '#8fd8ec');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H - GROUND_H);

    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    [[60, 90, 22], [95, 100, 16], [280, 60, 20], [320, 70, 14], [180, 130, 18]].forEach(([x, y, r]) => {
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(x + r * 0.9, y + 4, r * 0.7, 0, Math.PI * 2); ctx.fill();
    });
}

function drawGround() {
    ctx.fillStyle = '#ded895';
    ctx.fillRect(0, H - GROUND_H, W, GROUND_H);
    ctx.fillStyle = '#5cad3a';
    ctx.fillRect(0, H - GROUND_H, W, 12);
    ctx.fillStyle = '#4a8f2c';
    for (let x = -groundOffset; x < W; x += 24) {
        ctx.fillRect(x, H - GROUND_H, 12, 12);
    }
}

function drawPipes() {
    pipes.forEach(p => {
        ctx.fillStyle = '#4caf50';
        ctx.strokeStyle = '#2e7d32';
        ctx.lineWidth = 3;
        // top pipe
        ctx.fillRect(p.x, 0, PIPE_W, p.gapY);
        ctx.strokeRect(p.x, 0, PIPE_W, p.gapY);
        ctx.fillRect(p.x - 5, p.gapY - 24, PIPE_W + 10, 24);
        ctx.strokeRect(p.x - 5, p.gapY - 24, PIPE_W + 10, 24);
        // bottom pipe
        const bottomY = p.gapY + PIPE_GAP;
        ctx.fillRect(p.x, bottomY, PIPE_W, H - GROUND_H - bottomY);
        ctx.strokeRect(p.x, bottomY, PIPE_W, H - GROUND_H - bottomY);
        ctx.fillRect(p.x - 5, bottomY, PIPE_W + 10, 24);
        ctx.strokeRect(p.x - 5, bottomY, PIPE_W + 10, 24);
    });
}

function drawBird() {
    const angle = Math.max(-0.5, Math.min(1.2, bird.vy / 10));
    const r = bird.r + 3;
    ctx.save();
    ctx.translate(bird.x, bird.y);
    ctx.rotate(angle);

    // ear tufts
    ctx.fillStyle = '#7a5230';
    ctx.beginPath();
    ctx.moveTo(-r * 0.7, -r * 0.7);
    ctx.lineTo(-r * 0.3, -r * 1.5);
    ctx.lineTo(-r * 0.05, -r * 0.6);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(r * 0.7, -r * 0.7);
    ctx.lineTo(r * 0.3, -r * 1.5);
    ctx.lineTo(r * 0.05, -r * 0.6);
    ctx.fill();

    // body (owl brown)
    ctx.fillStyle = '#8a5a34';
    ctx.beginPath();
    ctx.arc(0, 0, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#5c3a1e';
    ctx.lineWidth = 2;
    ctx.stroke();

    // pale belly patch
    ctx.fillStyle = '#e4c9a3';
    ctx.beginPath();
    ctx.ellipse(1, r * 0.35, r * 0.62, r * 0.55, 0, 0, Math.PI * 2);
    ctx.fill();

    // wing
    ctx.fillStyle = '#6d4526';
    ctx.beginPath();
    ctx.ellipse(-4, 3, 8, 6, Math.sin(frame * 0.3) * 0.3, 0, Math.PI * 2);
    ctx.fill();

    // big round owl eyes (white rings)
    [-6, 6].forEach((ex) => {
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(ex, -3, 6.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#5c3a1e';
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.fillStyle = '#2b1a0e';
        ctx.beginPath();
        ctx.arc(ex + 1.5, -3, 3, 0, Math.PI * 2);
        ctx.fill();
    });

    // beak
    ctx.fillStyle = '#ff8c1a';
    ctx.beginPath();
    ctx.moveTo(-3, 1);
    ctx.lineTo(3, 1);
    ctx.lineTo(0, 6);
    ctx.fill();
    ctx.restore();
}

function drawScore() {
    ctx.fillStyle = '#fff';
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 3;
    ctx.font = 'bold 40px Segoe UI';
    ctx.textAlign = 'center';
    ctx.strokeText(score, W / 2, 70);
    ctx.fillText(score, W / 2, 70);
}

function drawOverlay() {
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(0, 0, W, H - GROUND_H);
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';
    if (state === 'ready') {
        ctx.font = 'bold 26px Segoe UI';
        ctx.fillText('Sammy the Owl', W / 2, H / 2 - 40);
        ctx.font = '16px Segoe UI';
        ctx.fillText('Click, tap, or press Space', W / 2, H / 2);
        ctx.fillText('to start flapping', W / 2, H / 2 + 22);
    } else if (state === 'gameover') {
        ctx.font = 'bold 30px Segoe UI';
        ctx.fillText('Sammy took a rest', W / 2, H / 2 - 50);
        ctx.font = 'bold 20px Segoe UI';
        ctx.fillText('Score: ' + score, W / 2, H / 2 - 12);
        ctx.fillText('Best: ' + best, W / 2, H / 2 + 16);
        ctx.font = '16px Segoe UI';
        ctx.fillText('Click / tap / Space to retry', W / 2, H / 2 + 50);
    }
}

function loop() {
    update();
    drawBackground();
    drawPipes();
    drawGround();
    drawBird();
    drawScore();
    if (state !== 'playing') drawOverlay();
    requestAnimationFrame(loop);
}

loop();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE
