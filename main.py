import time
from agent.ingestor import load_invoices
from agent.trigger_logic import get_stage
from agent.email_generator import generate_email
from agent.audit_logger import init_db, log_entry

def run_agent():
    init_db()
    invoices = load_invoices('data/invoices.csv')

    print("\n========== CREDIT FOLLOW-UP AGENT (DRY RUN) ==========\n")

    for _, invoice in invoices.iterrows():
        stage = get_stage(invoice['days_overdue'])

        print(f"Invoice : {invoice['invoice_no']}")
        print(f"Client  : {invoice['client_name']}")
        print(f"Amount  : Rs.{invoice['amount']:,}")
        print(f"Overdue : {invoice['days_overdue']} days")

        if stage == 'legal':
            print(f"Stage   : FLAGGED FOR LEGAL REVIEW — no email sent")
            log_entry(invoice, 'legal', 'N/A', 'FLAGGED_FOR_LEGAL')
        else:
            print(f"Stage   : {stage}")
            try:
                subject, body = generate_email(invoice, stage)
                print(f"Subject : {subject}")
                print(f"Body    :\n{body}")
                log_entry(invoice, stage, subject, 'DRY_RUN')
            except Exception as e:
                print(f"Error generating email: {e}")
                log_entry(invoice, stage, 'ERROR', 'FAILED')
            time.sleep(2)

        print("-" * 55 + "\n")

if __name__ == "__main__":
    run_agent()