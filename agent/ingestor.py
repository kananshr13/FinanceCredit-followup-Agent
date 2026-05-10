import pandas as pd
from datetime import date

def load_invoices(filepath):
    df = pd.read_csv(filepath)
    df['due_date'] = pd.to_datetime(df['due_date'])
    today = pd.Timestamp(date.today())
    df['days_overdue'] = (today - df['due_date']).dt.days
    overdue = df[df['days_overdue'] > 0].copy()
    return overdue