# finance-app

A loan payment calculator: a FastAPI backend and a single-page form UI that
computes monthly payment, total paid, and total interest from loan amount,
annual interest rate, and loan period.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install finance-app@mgmt803
```

Then ask Claude to scaffold the app, or to adapt it (different fields,
different formula, extra charts, etc.).

## What it bundles

- `app.py` — FastAPI app with `GET /` (serves the form) and
  `POST /api/monthly-payment` (amortization math).
- `templates/index.html` — the form.
- `static/style.css`, `static/app.js` — styling and the fetch call that
  renders the result.
- `requirements.txt` — fastapi, uvicorn, jinja2, itsdangerous,
  python-multipart.

Run it with `uvicorn app:app --host 0.0.0.0 --port 8000` from the copied
folder.
