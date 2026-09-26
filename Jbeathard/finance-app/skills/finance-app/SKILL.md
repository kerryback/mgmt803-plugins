---
name: finance-app
description: >-
  Scaffold a loan payment calculator web app: a FastAPI backend that computes
  monthly payment, total paid, and total interest from loan amount, annual
  interest rate, and loan period in years, plus a matching form UI. Trigger on
  "build a loan calculator", "make a mortgage/loan payment app", "monthly
  payment calculator", or when adapting this app to new fields or a different
  amortization formula.
license: MIT
---

# finance-app

Produce a small FastAPI app with one form and one calculation endpoint. Two
files worth knowing before you touch anything:

- `app.py` — `GET /` renders the form; `POST /api/monthly-payment` takes
  `loan_amount`, `interest_rate` (annual %), `loan_period_years` as form
  fields and returns `monthly_payment`, `total_paid`, `total_interest` as
  JSON. Standard amortization formula, with a zero-rate special case.
- `static/app.js` — submits the form via `fetch`, replaces `#loan-result`
  with a `.result-grid` of `.stat` cards, or an `.error-text` div if the
  backend returns `{"error": ...}`.

## Workflow

1. **Copy the template** into the target project directory (keep the
   relative layout — `app.py` expects `templates/` and `static/` next to it):
   ```
   cp -r "$SKILL_DIR/assets/." <target-dir>/
   ```
2. **Adapt the fields** if asked for something beyond the three inputs
   (extra fees, down payment, variable rate, amortization schedule table,
   etc.): edit the form in `templates/index.html`, the endpoint in `app.py`,
   and the render logic in `static/app.js` together — they're a matched set.
3. **Install and run**, following this workspace's web-app convention:
   ```
   pip install -r requirements.txt
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   Bind `0.0.0.0`, not `127.0.0.1` — required for the app to be reachable
   outside the container.
4. **Verify** by loading the page and submitting the form with a real
   number before calling it done.

## Notes

- The math: `r = (annual_rate/100)/12`, `n = years*12`,
  `payment = principal * r / (1 - (1+r)**-n)`, falling back to
  `principal/n` when `r == 0`. Validate `loan_amount > 0`,
  `loan_period_years > 0`, `interest_rate >= 0` before computing.
- Keep frontend URLs relative (`static/style.css`, `api/monthly-payment`,
  no leading slash) so the app works when served under a sub-path.
