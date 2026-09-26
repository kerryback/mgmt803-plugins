from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>F1 Racer</title>
<style>
    * { box-sizing: border-box; }
    body {
        margin: 0;
        min-height: 100vh;
        font-family: 'Segoe UI', sans-serif;
        background: #0a0a0a;
        color: #fff;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 16px;
    }
    h1 { margin: 0 0 6px; font-size: 1.5rem; }
    .subtitle { color: #bbb; font-size: 0.85rem; margin-bottom: 12px; text-align: center; }
    canvas {
        background: #3f7d3f;
        border-radius: 12px;
        box-shadow: 0 20px 45px rgba(0,0,0,0.6);
        max-width: 100%;
        height: auto;
        outline: none;
    }
</style>
</head>
<body>
    <h1>&#127937; F1 Racer</h1>
    <div class="subtitle">Arrow keys or WASD to drive &mdash; 3 laps against 2 rivals</div>
    <canvas id="game" width="1000" height="650" tabindex="0"></canvas>

<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height;
const TOP_BAR = 60;
const TRACK_WIDTH = 90;
const TOTAL_LAPS = 3;

const WAYPOINTS = [
    { x: 150, y: 550 },
    { x: 850, y: 550 },
    { x: 930, y: 470 },
    { x: 930, y: 250 },
    { x: 850, y: 170 },
    { x: 650, y: 170 },
    { x: 600, y: 230 },
    { x: 650, y: 290 },
    { x: 500, y: 340 },
    { x: 300, y: 340 },
    { x: 200, y: 280 },
    { x: 100, y: 200 },
    { x: 70, y: 350 },
    { x: 100, y: 480 },
];

function mid(a, b) { return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; }
function sub(a, b) { return { x: a.x - b.x, y: a.y - b.y }; }
function norm(v) { const l = Math.hypot(v.x, v.y) || 1; return { x: v.x / l, y: v.y / l }; }
function quadPoint(p0, p1, p2, t) {
    const it = 1 - t;
    return {
        x: it * it * p0.x + 2 * it * t * p1.x + t * t * p2.x,
        y: it * it * p0.y + 2 * it * t * p1.y + t * t * p2.y,
    };
}

function buildTrack(pts, stepsPerSeg) {
    const n = pts.length;
    const dense = [];
    for (let i = 0; i < n; i++) {
        const start = mid(pts[(i - 1 + n) % n], pts[i]);
        const control = pts[i];
        const end = mid(pts[i], pts[(i + 1) % n]);
        for (let s = 0; s < stepsPerSeg; s++) {
            dense.push(quadPoint(start, control, end, s / stepsPerSeg));
        }
    }
    return dense;
}

const TRACK = buildTrack(WAYPOINTS, 24);
const N = TRACK.length;

function drawTrackPath(widthOverride) {
    ctx.beginPath();
    const n = WAYPOINTS.length;
    const m0 = mid(WAYPOINTS[n - 1], WAYPOINTS[0]);
    ctx.moveTo(m0.x, m0.y);
    for (let i = 0; i < n; i++) {
        const p1 = WAYPOINTS[i];
        const p2 = WAYPOINTS[(i + 1) % n];
        const m = mid(p1, p2);
        ctx.quadraticCurveTo(p1.x, p1.y, m.x, m.y);
    }
    ctx.closePath();
    ctx.lineWidth = widthOverride;
    ctx.stroke();
}

function drawTrack() {
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#c0392b';
    drawTrackPath(TRACK_WIDTH + 22);
    ctx.setLineDash([22, 22]);
    ctx.strokeStyle = '#fff';
    drawTrackPath(TRACK_WIDTH + 22);
    ctx.setLineDash([]);
    ctx.strokeStyle = '#3a3a3a';
    drawTrackPath(TRACK_WIDTH);
    ctx.strokeStyle = '#555';
    ctx.setLineDash([14, 18]);
    ctx.lineWidth = 2;
    ctx.beginPath();
    const n = WAYPOINTS.length;
    const m0 = mid(WAYPOINTS[n - 1], WAYPOINTS[0]);
    ctx.moveTo(m0.x, m0.y);
    for (let i = 0; i < n; i++) {
        const p1 = WAYPOINTS[i];
        const p2 = WAYPOINTS[(i + 1) % n];
        const m = mid(p1, p2);
        ctx.quadraticCurveTo(p1.x, p1.y, m.x, m.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
}

function drawStartLine() {
    const p = TRACK[0];
    const dir = norm(sub(TRACK[6], TRACK[N - 6]));
    const angle = Math.atan2(dir.y, dir.x);
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(angle);
    const squares = 8, sq = TRACK_WIDTH / squares;
    for (let i = 0; i < squares; i++) {
        ctx.fillStyle = (i % 2 === 0) ? '#fff' : '#111';
        ctx.fillRect(-5, -TRACK_WIDTH / 2 + i * sq, 10, sq);
    }
    ctx.restore();
}

function makeCar(color, isPlayer) {
    const dir = norm(sub(TRACK[5], TRACK[0]));
    const perp = { x: -dir.y, y: dir.x };
    const angle = Math.atan2(dir.y, dir.x);
    return {
        color, isPlayer,
        x: TRACK[0].x, y: TRACK[0].y,
        angle, speed: 0,
        nearestIndex: 0, prevIndex: 0, hasLeftStart: false,
        offTrack: false,
        lapCount: 0, lapStartTime: 0, lastLap: null, bestLap: null,
        smoke: [],
    };
}

let player, rivals, cars, phase, countdownVal, countdownUntil, raceStartTime, playAgainBtn;

function positionGrid() {
    const dir = norm(sub(TRACK[5], TRACK[0]));
    const perp = { x: -dir.y, y: dir.x };
    const angle = Math.atan2(dir.y, dir.x);
    const place = (car, lateral, back) => {
        car.x = TRACK[0].x + perp.x * lateral - dir.x * back;
        car.y = TRACK[0].y + perp.y * lateral - dir.y * back;
        car.angle = angle;
        car.speed = 0;
        car.nearestIndex = 0; car.prevIndex = 0; car.hasLeftStart = false;
        car.lapCount = 0; car.lastLap = null; car.bestLap = null; car.smoke = [];
    };
    place(player, 0, 0);
    place(rivals[0], 24, 26);
    place(rivals[1], -24, 52);
}

function resetRace() {
    player = makeCar('#e63946', true);
    rivals = [makeCar('#1d8bd1', false), makeCar('#f4c93a', false)];
    cars = [player, ...rivals];
    positionGrid();
    phase = 'countdown';
    countdownVal = 3;
    countdownUntil = performance.now() + 800;
}
resetRace();

function findNearest(car) {
    let searchIdx;
    const win = 55;
    searchIdx = [];
    for (let d = -win; d <= win; d++) searchIdx.push(((car.nearestIndex + d) % N + N) % N);
    let best = Infinity, bestIdx = car.nearestIndex;
    searchIdx.forEach(i => {
        const p = TRACK[i];
        const dx = car.x - p.x, dy = car.y - p.y;
        const d = dx * dx + dy * dy;
        if (d < best) { best = d; bestIdx = i; }
    });
    car.distToTrack = Math.sqrt(best);
    car.offTrack = car.distToTrack > TRACK_WIDTH / 2;
    car.nearestIndex = bestIdx;
}

function updateLap(car, now) {
    if (car.nearestIndex > N * 0.2) car.hasLeftStart = true;
    if (car.hasLeftStart && car.prevIndex > N * 0.75 && car.nearestIndex < N * 0.25) {
        car.lapCount++;
        const lapTime = now - car.lapStartTime;
        car.lastLap = lapTime;
        if (!car.bestLap || lapTime < car.bestLap) car.bestLap = lapTime;
        car.lapStartTime = now;
        car.hasLeftStart = false;
    }
    car.prevIndex = car.nearestIndex;
}

function rubberBandFactor(car) {
    const playerProgress = player.lapCount * N + player.nearestIndex;
    const carProgress = car.lapCount * N + car.nearestIndex;
    const diff = carProgress - playerProgress;
    const t = Math.max(-1, Math.min(1, diff / (N * 1.2)));
    return 1 - t * 0.28;
}

function physics(car, accelInput, steerInput, speedMultiplier) {
    const mult = speedMultiplier || 1;
    const maxSpeed = (car.offTrack ? 3 : 6.4) * mult;
    if (accelInput > 0) car.speed += 0.16;
    else if (accelInput < 0) car.speed -= 0.3;
    else car.speed *= 0.985;
    car.speed *= car.offTrack ? 0.96 : 0.995;
    car.speed = Math.max(-maxSpeed * 0.5, Math.min(maxSpeed, car.speed));
    const turnFactor = Math.min(Math.abs(car.speed) / maxSpeed, 1) * (car.speed < 0 ? -1 : 1);
    car.angle += steerInput * 0.045 * turnFactor;
    car.x += Math.cos(car.angle) * car.speed;
    car.y += Math.sin(car.angle) * car.speed;

    if (car.offTrack && Math.abs(car.speed) > 1 && Math.random() < 0.6) {
        car.smoke.push({ x: car.x - Math.cos(car.angle) * 14, y: car.y - Math.sin(car.angle) * 14, life: 24 });
    }
    car.smoke.forEach(p => p.life--);
    car.smoke = car.smoke.filter(p => p.life > 0);
}

const AI_BASE_FACTOR = 0.9;

function aiDrive(car) {
    const lookahead = 26;
    const target = TRACK[(car.nearestIndex + lookahead) % N];
    const desired = Math.atan2(target.y - car.y, target.x - car.x);
    let diff = desired - car.angle + (Math.random() - 0.5) * 0.1;
    while (diff > Math.PI) diff -= Math.PI * 2;
    while (diff < -Math.PI) diff += Math.PI * 2;
    const steerInput = Math.max(-1, Math.min(1, diff * 1.7));
    const speedFrac = Math.abs(car.speed) / (car.offTrack ? 3 : 6.4);
    const speedTarget = Math.max(0.4, 1 - Math.min(1, Math.abs(diff) * 1.3));
    const accelInput = speedFrac < speedTarget ? 1 : (Math.abs(diff) > 0.5 ? -0.4 : 0.05);
    const speedMultiplier = AI_BASE_FACTOR * rubberBandFactor(car);
    return { accelInput, steerInput, speedMultiplier };
}

const keys = {};
window.addEventListener('keydown', (e) => {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
    keys[e.code] = true;
    startAudio();
});
window.addEventListener('keyup', (e) => { keys[e.code] = false; });

function playerInput() {
    const up = keys['ArrowUp'] || keys['KeyW'];
    const down = keys['ArrowDown'] || keys['KeyS'];
    const left = keys['ArrowLeft'] || keys['KeyA'];
    const right = keys['ArrowRight'] || keys['KeyD'];
    return {
        accelInput: up ? 1 : (down ? -1 : 0),
        steerInput: left ? -1 : (right ? 1 : 0),
    };
}

let audioCtx, osc, gainNode, audioStarted = false;
function startAudio() {
    if (audioStarted) return;
    audioStarted = true;
    try {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        osc = audioCtx.createOscillator();
        gainNode = audioCtx.createGain();
        osc.type = 'sawtooth';
        gainNode.gain.value = 0.025;
        osc.connect(gainNode).connect(audioCtx.destination);
        osc.start();
    } catch (e) { /* audio unavailable, ignore */ }
}
function updateAudio() {
    if (!osc) return;
    const frac = Math.min(1, Math.abs(player.speed) / 6.4);
    osc.frequency.setTargetAtTime(70 + frac * 260, audioCtx.currentTime, 0.05);
}

function classify() {
    return [...cars].sort((a, b) => (b.lapCount + b.nearestIndex / N) - (a.lapCount + a.nearestIndex / N));
}

function update(now) {
    if (phase === 'countdown') {
        if (now > countdownUntil) {
            countdownVal--;
            countdownUntil = now + 800;
            if (countdownVal < 0) {
                phase = 'racing';
                raceStartTime = now;
                cars.forEach(c => c.lapStartTime = now);
            }
        }
        return;
    }
    if (phase !== 'racing') return;

    const pIn = playerInput();
    physics(player, pIn.accelInput, pIn.steerInput, 1);
    findNearest(player);
    updateLap(player, now);

    rivals.forEach(car => {
        const input = aiDrive(car);
        physics(car, input.accelInput, input.steerInput, input.speedMultiplier);
        findNearest(car);
        updateLap(car, now);
    });

    updateAudio();

    if (player.lapCount >= TOTAL_LAPS) {
        phase = 'finished';
    }
}

function drawGrass() {
    ctx.fillStyle = '#3f7d3f';
    ctx.fillRect(0, TOP_BAR, W, H - TOP_BAR);
    ctx.fillStyle = 'rgba(0,0,0,0.05)';
    for (let y = TOP_BAR; y < H; y += 40) ctx.fillRect(0, y, W, 20);
}

function drawSmoke(car) {
    car.smoke.forEach(p => {
        ctx.fillStyle = `rgba(150,120,90,${p.life / 24 * 0.5})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 6 + (24 - p.life) * 0.3, 0, Math.PI * 2);
        ctx.fill();
    });
}

function drawCar(car) {
    ctx.save();
    ctx.translate(car.x, car.y);
    ctx.rotate(car.angle);
    ctx.fillStyle = '#111';
    ctx.fillRect(-17, -12, 4, 24);
    ctx.fillStyle = '#111';
    [[8, -9], [8, 9], [-10, -9], [-10, 9]].forEach(([tx, ty]) => ctx.fillRect(tx - 3, ty - 2, 6, 4));
    ctx.fillStyle = car.color;
    ctx.beginPath();
    ctx.moveTo(17, 0);
    ctx.lineTo(6, -7);
    ctx.lineTo(-14, -6);
    ctx.lineTo(-14, 6);
    ctx.lineTo(6, 7);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.3)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = '#111';
    ctx.fillRect(14, -10, 4, 20);
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(-2, 0, 4, 3, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
}

function fmtTime(ms) {
    if (ms == null) return '--:--.-';
    const s = ms / 1000;
    const m = Math.floor(s / 60);
    const rem = (s - m * 60).toFixed(1).padStart(4, '0');
    return m + ':' + rem;
}

function drawHUD(now) {
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, W, TOP_BAR);
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'left';
    ctx.font = 'bold 18px Segoe UI';
    ctx.fillText('Lap ' + Math.min(player.lapCount + 1, TOTAL_LAPS) + ' / ' + TOTAL_LAPS, 20, 32);
    ctx.font = '13px Segoe UI';
    ctx.fillStyle = '#bbb';
    ctx.fillText('Best lap: ' + fmtTime(player.bestLap), 20, 50);

    const rank = classify().findIndex(c => c === player) + 1;
    ctx.textAlign = 'center';
    ctx.font = 'bold 22px Segoe UI';
    ctx.fillStyle = '#f4c93a';
    ctx.fillText(rank === 1 ? '1st' : rank === 2 ? '2nd' : '3rd', W / 2, 38);

    ctx.textAlign = 'right';
    ctx.font = 'bold 18px Segoe UI';
    ctx.fillStyle = '#fff';
    const elapsed = phase === 'racing' ? now - raceStartTime : (phase === 'finished' ? now - raceStartTime : 0);
    ctx.fillText(fmtTime(elapsed), W - 20, 32);
    ctx.font = '13px Segoe UI';
    ctx.fillStyle = '#bbb';
    ctx.fillText(player.offTrack ? 'OFF TRACK' : 'on track', W - 20, 50);
}

function drawOverlay(now) {
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(0, TOP_BAR, W, H - TOP_BAR);
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';

    if (phase === 'countdown') {
        ctx.font = 'bold 64px Segoe UI';
        ctx.fillText(countdownVal >= 0 ? String(countdownVal + 1) : 'GO!', W / 2, H / 2 + 20);
    } else if (phase === 'finished') {
        const rank = classify().findIndex(c => c === player) + 1;
        const label = rank === 1 ? '1st Place!' : rank === 2 ? '2nd Place' : '3rd Place';
        ctx.font = 'bold 30px Segoe UI';
        ctx.fillText('Race Finished \\u2014 ' + label, W / 2, 190);
        ctx.font = '18px Segoe UI';
        ctx.fillText('Total time: ' + fmtTime(raceStartTime ? performance.now() - raceStartTime : 0), W / 2, 230);
        ctx.fillText('Best lap: ' + fmtTime(player.bestLap), W / 2, 258);

        const btnW = 180, btnH = 46;
        playAgainBtn = { x: W / 2 - btnW / 2, y: 300, w: btnW, h: btnH };
        ctx.fillStyle = '#e63946';
        ctx.fillRect(playAgainBtn.x, playAgainBtn.y, playAgainBtn.w, playAgainBtn.h);
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 18px Segoe UI';
        ctx.fillText('Race Again', W / 2, playAgainBtn.y + 30);
    }
}

let finishedTimeSnapshot = null;
function draw(now) {
    drawGrass();
    drawTrack();
    drawStartLine();
    rivals.forEach(drawSmoke);
    drawSmoke(player);
    rivals.forEach(drawCar);
    drawCar(player);
    drawHUD(now);
    if (phase !== 'racing') drawOverlay(now);
}

function loop(now) {
    update(now);
    draw(now);
    requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

canvas.addEventListener('mousedown', (e) => {
    if (phase === 'finished' && playAgainBtn) {
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (canvas.height / rect.height);
        if (x > playAgainBtn.x && x < playAgainBtn.x + playAgainBtn.w &&
            y > playAgainBtn.y && y < playAgainBtn.y + playAgainBtn.h) {
            resetRace();
        }
    }
    canvas.focus();
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE
