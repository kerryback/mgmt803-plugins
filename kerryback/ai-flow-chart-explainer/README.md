# AI Flow Chart Explainer

A local interactive guide to the included diagram, **How agents, skills, tools, and APIs connect**. Select a region of the chart to see what it means and how it connects to the rest of the workflow. The original PNG is included unchanged and is available from the app by itself.

## Run

From this folder:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:8008. If Python is installed as `python` rather than `py`, use `python` in those commands.

The app runs locally and uses no API key. Use **Open original PNG** in the header to see the source image alone, or **Download PNG** to save it.

## Files

- `app.py`: FastAPI server
- `index.html`: interactive explainer
- `AI Flow chart Tool.png`: original source image
