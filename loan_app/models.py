from . import mysql

def save_calculation(amount, rate, period, term, method, total_payment, total_interest, payment):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO loan_history (amount, rate, period, term, payment_method, total_payment, total_interest, periodic_payment)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (amount, rate, period, term, method, total_payment, total_interest, payment))
    mysql.connection.commit()
    cur.close()