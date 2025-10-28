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
        total_interest = 0.0

        for i in range(1, total_payments + 1):
            interest = balance * r
            principal = payment - interest
            balance -= principal
            total_interest += interest
            schedule.append({
                'period': i,
                'payment': round(payment, 2),
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'balance': round(balance if balance > 0 else 0, 2)
            })

        total_payment = payment * total_payments

        total_interest = total_payment - amount
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


@main.route('/export_pdf', methods=['POST'])
def export_pdf():
    schedule = request.form.get('schedule')
    df = pd.read_json(schedule)
    output = BytesIO()

    # Create a full-width page layout
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        leftMargin=36,   # small margins for full-width layout
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = 1  # 1 = center alignment

    # Create centered title
    title = Paragraph("Loan Amortization Schedule", title_style)

    # Prepare table data
    data = [["Period", "Payment", "Principal", "Interest", "Balance"]]
    for _, row in df.iterrows():
        data.append([
            f"{row['period']}",
            f"${row['payment']:.2f}",
            f"${row['principal']:.2f}",
            f"${row['interest']:.2f}",
            f"${row['balance']:.2f}"
        ])

    # Calculate full-page table width
    page_width = letter[0] - (doc.leftMargin + doc.rightMargin)
    col_widths = [page_width * w for w in [0.12, 0.22, 0.22, 0.22, 0.22]]

    # Create table with full width
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    # Build the document with centered title + full table
    elements = [title, table]
    doc.build(elements)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name='loan_schedule.pdf')
