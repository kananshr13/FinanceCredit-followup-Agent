import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'audit.db')

def mask_email(email):
    parts = email.split('@')
    return parts[0][0] + '***@' + parts[1]

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            invoice_no TEXT,
            client_name TEXT,
            amount REAL,
            days_overdue INTEGER,
            stage TEXT,
            subject TEXT,
            send_status TEXT,
            contact_email_masked TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_entry(invoice, stage, subject, send_status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_log 
        (timestamp, invoice_no, client_name, amount, days_overdue, stage, subject, send_status, contact_email_masked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        invoice['invoice_no'],
        invoice['client_name'],
        invoice['amount'],
        invoice['days_overdue'],
        str(stage),
        subject,
        send_status,
        mask_email(invoice['contact_email'])
    ))
    conn.commit()
    conn.close()