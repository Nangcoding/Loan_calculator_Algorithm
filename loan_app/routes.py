from flask import Blueprint, render_template, request
from .models import Loan

main = Blueprint('main', __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    summary = None
    if request.method == "POST":
        principal = float(request.form.get("principal", 0))
        rate = float(request.form.get("rate", 0))
        years = int(request.form.get("years", 0))

        loan = Loan(principal, rate, years)

        summary = {
            "principal": principal,
            "rate": rate,
            "years": years,
            "monthly_payment": loan.monthly_payment(),
            "total_payment": loan.total_payment(),
            "total_interest": loan.total_interest()
        }

    return render_template("index.html", summary=summary)
