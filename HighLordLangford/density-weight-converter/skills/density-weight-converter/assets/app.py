from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

GRAMS_PER_POUND = 453.59237
CM3_PER_FT3 = 28316.846592
SQFT_PER_ACRE = 43560
POUNDS_PER_TON = 2000

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Density to Weight Converter</title>
<style>
  :root {
    --ink: #1c2530;
    --muted: #5b6675;
    --accent: #2563eb;
    --border: #e2e6ec;
    --panel: #f8fafc;
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    max-width: 480px;
    margin: 48px auto;
    color: var(--ink);
    background: #fff;
  }
  h1 {
    font-size: 1.4em;
    margin-bottom: 4px;
  }
  p.subtitle {
    color: var(--muted);
    font-size: 0.92em;
    margin-top: 0;
    line-height: 1.5;
  }
  .card {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin-top: 16px;
  }
  label {
    display: block;
    margin-top: 14px;
    font-weight: 600;
    font-size: 0.88em;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  input[type="number"] {
    width: 100%;
    padding: 9px 10px;
    margin-top: 6px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 1em;
    color: var(--ink);
  }
  input[type="number"]:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
  }
  .checkbox-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 18px;
    font-weight: normal;
    text-transform: none;
    color: var(--ink);
    font-size: 0.95em;
    letter-spacing: normal;
  }
  .checkbox-row input { width: auto; margin: 0; }
  button {
    margin-top: 22px;
    padding: 10px 20px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 0.95em;
    font-weight: 600;
    cursor: pointer;
  }
  button:hover { background: #1d4ed8; }

  #result:empty { margin: 0; }
  .result-panel {
    margin-top: 22px;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  .result-panel .step {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 11px 16px;
    font-size: 0.86em;
    color: var(--muted);
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    font-family: "SF Mono", Consolas, monospace;
  }
  .result-panel .step .eq { color: var(--ink); }
  .result-panel .final {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: #fff;
  }
  .result-panel .final .label {
    font-size: 0.85em;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .result-panel .final .value {
    font-size: 1.4em;
    font-weight: 700;
    color: var(--accent);
  }
  .error-msg {
    margin-top: 22px;
    padding: 12px 16px;
    border-radius: 8px;
    background: #fef2f2;
    color: #b91c1c;
    font-size: 0.9em;
  }
</style>
</head>
<body>
  <h1>Density &rarr; Weight Converter</h1>
  <p class="subtitle">Converting a density (g/cm&sup3;) to a weight in pounds requires
     a volume as well, since weight = density &times; volume.</p>

  <div class="card">
    <label for="density">Density (g/cm&sup3;)</label>
    <input type="number" id="density" step="any" placeholder="e.g. 7.87 for steel">

    <label class="checkbox-row">
      <input type="checkbox" id="tonsPerAcre" onchange="toggleMode()">
      Convert to tons per acre
    </label>

    <div id="volumeFields">
      <label for="volume">Volume (ft&sup3;)</label>
      <input type="number" id="volume" step="any" placeholder="e.g. 1">
    </div>

    <div id="acreFields" style="display: none;">
      <label for="thickness">Thickness (ft)</label>
      <input type="number" id="thickness" step="any" placeholder="e.g. 0.5">

      <label for="acres">Acres</label>
      <input type="number" id="acres" step="any" placeholder="e.g. 10">
    </div>

    <button onclick="convert()">Convert</button>
  </div>

  <div id="result"></div>

<script>
function toggleMode() {
  const isTonsPerAcre = document.getElementById("tonsPerAcre").checked;
  document.getElementById("volumeFields").style.display = isTonsPerAcre ? "none" : "block";
  document.getElementById("acreFields").style.display = isTonsPerAcre ? "block" : "none";
  document.getElementById("result").innerHTML = "";
}

function showError(message) {
  document.getElementById("result").innerHTML = `<div class="error-msg">${message}</div>`;
}

async function convert() {
  const density = parseFloat(document.getElementById("density").value);
  const isTonsPerAcre = document.getElementById("tonsPerAcre").checked;
  const resultDiv = document.getElementById("result");
  const payload = { density: density };

  if (isTonsPerAcre) {
    const thickness = parseFloat(document.getElementById("thickness").value);
    const acres = parseFloat(document.getElementById("acres").value);
    if (isNaN(density) || isNaN(thickness) || isNaN(acres)) {
      showError("Please enter density, thickness, and acres.");
      return;
    }
    payload.thickness = thickness;
    payload.acres = acres;
  } else {
    const volume = parseFloat(document.getElementById("volume").value);
    if (isNaN(density) || isNaN(volume)) {
      showError("Please enter both density and volume.");
      return;
    }
    payload.volume = volume;
  }

  const response = await fetch("calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (isTonsPerAcre) {
    const thickness = payload.thickness;
    const acres = payload.acres;
    resultDiv.innerHTML = `
      <div class="result-panel">
        <div class="step"><span>Volume</span><span class="eq">${thickness} ft &times; ${acres} acres &times; 43,560 ft&sup2;/acre = ${data.volume_ft3.toFixed(2)} ft&sup3;</span></div>
        <div class="step"><span>Weight</span><span class="eq">${density} g/cm&sup3; &times; ${data.volume_ft3.toFixed(2)} ft&sup3; &times; 28,316.85 cm&sup3;/ft&sup3; &divide; 453.59 g/lb = ${data.pounds.toFixed(2)} lb</span></div>
        <div class="step"><span>Tons</span><span class="eq">${data.pounds.toFixed(2)} lb &divide; 2,000 lb/ton = ${data.tons.toFixed(4)} tons</span></div>
        <div class="final">
          <span class="label">Tons per acre</span>
          <span class="value">${Math.round(data.tons_per_acre).toLocaleString()}</span>
        </div>
      </div>
    `;
  } else {
    resultDiv.innerHTML = `
      <div class="result-panel">
        <div class="final">
          <span class="label">Weight</span>
          <span class="value">${data.pounds.toFixed(4)} lb</span>
        </div>
      </div>
    `;
  }
}
</script>
</body>
</html>
"""


class ConversionInput(BaseModel):
    density: float
    volume: float | None = None
    thickness: float | None = None
    acres: float | None = None


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


@app.post("/calculate")
def calculate(data: ConversionInput):
    if data.thickness is not None and data.acres is not None:
        volume_ft3 = data.thickness * data.acres * SQFT_PER_ACRE
        mass_grams = data.density * volume_ft3 * CM3_PER_FT3
        pounds = mass_grams / GRAMS_PER_POUND
        tons = pounds / POUNDS_PER_TON
        tons_per_acre = tons / data.acres
        return {
            "pounds": pounds,
            "tons_per_acre": tons_per_acre,
            "volume_ft3": volume_ft3,
            "tons": tons,
        }

    mass_grams = data.density * data.volume * CM3_PER_FT3
    pounds = mass_grams / GRAMS_PER_POUND
    return {"pounds": pounds}
