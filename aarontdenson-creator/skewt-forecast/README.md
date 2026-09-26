# skewt-forecast

An interactive Skew-T forecast app for airports or custom coordinates. Airport code edits and airport selections load automatically. Select forecast hours through the next 24 hours, inspect temperature and dewpoint in Celsius, and move over the profile for interpolated altitude and pressure. Wind barbs use meteorological from-directions: 360° up, 090° right, 180° down, and 270° left.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install skewt-forecast@mgmt803
```

Then ask Claude to set up or launch the forecast Skew-T app.

## Run directly

Copy the files from `skills/skewt-forecast/assets/` to a folder, run `python server.py`, and open http://127.0.0.1:8000. Python 3 and an internet connection are required. The app uses Open-Meteo pressure-level forecasts and needs no API key for personal use.

These are model forecast profiles, not observed radiosonde launches. Available pressure levels and model resolution vary by location.
