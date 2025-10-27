from flask import Blueprint, render_template, request, send_file
from io import BytesIO
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from .models import save_calculation

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/calculator.html', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        rate = float(request.form['rate'])
        period = request.form['period']
        term = int(request.form['term'])
        method = request.form['method']

        if period == 'Monthly':
            n = 12
        elif period == 'Quarterly':
            n = 4
        else:
            n = 1

        total_payments = n * term
        r = (rate / 100) / n

        if method == 'Annuity':
            if r == 0:
                payment = amount / total_payments
            else:
                payment = amount * (r * (1 + r)**total_payments) / ((1 + r)**total_payments - 1)
        else:
            payment = (amount / total_payments) + (amount * r)

        schedule = []
        balance = amount
        total_interest = 0

        for i in range(1, total_payments + 1):
            interest = balance * r
            principal = payment - interest
            balance -= principal
            if balance < 0: balance = 0
            total_interest += interest
            schedule.append({
                'period': i,
                'payment': round(payment, 2),
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'balance': round(balance, 2)
            })

        total_payment = payment * total_payments

        save_calculation(amount, rate, period, term, method, total_payment, total_interest, payment)

        return render_template(
            './calculator.html',
            payment=round(payment, 2),
            total_interest=round(total_interest, 2),
            total_payment=round(total_payment, 2),
            schedule=schedule
        )

    return render_template('calculator.html')

# ----- Export Excel -----
@main.route('/export_excel', methods=['POST'])
def export_excel():
    schedule = request.form.get('schedule')
    df = pd.read_json(schedule)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='loan_schedule.xlsx')

# ----- Export PDF -----
@main.route('/export_pdf', methods=['POST'])
def export_pdf():
    schedule = request.form.get('schedule')
    df = pd.read_json(schedule)
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()

    data = [["Period", "Payment", "Principal", "Interest", "Balance"]]
    for _, row in df.iterrows():
        data.append([
            row['period'],
            f"${row['payment']}",
            f"${row['principal']}",
            f"${row['interest']}",
            f"${row['balance']}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black)
    ]))

    doc.build([Paragraph("Loan Amortization Schedule", styles["Heading1"]), table])
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='loan_schedule.pdf')
