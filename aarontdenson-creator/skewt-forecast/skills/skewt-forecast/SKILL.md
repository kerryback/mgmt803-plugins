---
name: skewt-forecast
description: >-
  Set up, launch, or adapt an interactive 24-hour forecast Skew-T web app for
  airports or custom coordinates. Shows Celsius temperature and dewpoint,
  winds in knots, and an altitude/pressure readout under the pointer. Trigger
  on requests to make or launch a Skew-T or forecast sounding app.
license: MIT
---

# skewt-forecast

Provide an interactive local Skew-T forecast viewer. The bundled page fetches pressure-level temperature, dewpoint, wind speed/direction, and geopotential height from Open-Meteo. It plots hourly profiles for the next 24 hours, draws temperature/dewpoint traces and wind barbs, and interpolates altitude and pressure at the pointer.

## Set up or launch

1. Copy the bundled files into a project directory, keeping them together:
   ```
   cp -r "$SKILL_DIR/assets/." <target-dir>/
   ```
2. Start the local server from that directory:
   ```
   python server.py
   ```
3. Open http://127.0.0.1:8000. The page needs an internet connection for forecast data.
4. Type a listed airport ICAO code; the forecast loads automatically once the code is complete. Selecting an airport name also loads it automatically. If the station is not listed, type latitude and longitude in the search field.

## Conventions

- Temperatures are Celsius; wind speed is knots.
- Wind direction is meteorological (where wind comes from). The barb shaft points to its heading: 360° north/up, 090° east/right, 180° south/down, 270° west/left.
- The chart uses pressure-level model forecasts interpolated between levels; these are not observed balloon soundings. Do not describe forecast values as measurements.
- The chart marks the model's 0°C altitude. A red cursor alert marks saturated model air below freezing, but this does not confirm aircraft icing or supercooled liquid water; point users to current official icing forecasts.
- Surface/API errors should be shown to the user; never invent fallback weather values.
- The bundled server binds to 127.0.0.1 by default.
