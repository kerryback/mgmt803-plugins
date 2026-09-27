---
name: ai-flow-chart-explainer
description: >-
  Launch the AI Flow Chart Explainer when someone asks to understand the
  included chart about agents, skills, tools, plugins, MCP connectors, APIs,
  and external systems, or asks to open the original AI flow chart PNG.
---

# AI Flow Chart Explainer

The app lives two directories above this skill file. It contains the original
`AI Flow chart Tool.png` and an interactive explanation of the diagram.

From the app directory, install and launch it:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:8008. The app has direct links to view or download the
original PNG. The app is local, requires no API key, and should not be exposed
as a public server.
