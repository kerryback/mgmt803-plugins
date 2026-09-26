from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/api/monthly-payment")
def monthly_payment(
    loan_amount: float = Form(...),
    interest_rate: float = Form(...),
    loan_period_years: float = Form(...),
):
    if loan_amount <= 0 or loan_period_years <= 0 or interest_rate < 0:
        return {"error": "Loan amount and period must be positive, and rate cannot be negative."}

    n = loan_period_years * 12
    r = (interest_rate / 100) / 12

    if r == 0:
        payment = loan_amount / n
    else:
        payment = loan_amount * r / (1 - (1 + r) ** (-n))

    total_paid = payment * n
    total_interest = total_paid - loan_amount

    return {
        "monthly_payment": round(payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
    }
