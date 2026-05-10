import streamlit as st
import pandas as pd
import sqlite3
import time
import os
from agent.ingestor import load_invoices
from agent.trigger_logic import get_stage
from agent.email_generator import generate_email
from agent.audit_logger import init_db, log_entry

DB_PATH = os.path.join('logs', 'audit.db')

st.set_page_config(page_title="Credit Follow-Up Agent", page_icon="none", layout="wide")

st.markdown("""
<style>
.email-card {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 15px;
}
.email-header {
    border-bottom: 1px solid #333;
    padding-bottom: 10px;
    margin-bottom: 15px;
}
.email-field {
    color: #aaa;
    font-size: 13px;
    margin-bottom: 5px;
}
.email-field span {
    color: #fff;
    font-weight: 500;
}
.email-subject {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin: 10px 0;
}
.email-body {
    color: #ddd;
    font-size: 14px;
    line-height: 1.8;
    white-space: pre-wrap;
}
.stage-warm { color: #00c49f; font-weight: 600; }
.stage-firm { color: #ffbb28; font-weight: 600; }
.stage-formal { color: #ff8042; font-weight: 600; }
.stage-stern { color: #ff4444; font-weight: 600; }
.stage-legal { color: #aaaaaa; font-weight: 600; }
.sent-badge {
    background-color: #1a3a1a;
    color: #00c49f;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.legal-badge {
    background-color: #3a1a1a;
    color: #ff4444;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

def get_audit_log():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM audit_log ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def get_stage_label(stage):
    labels = {
        1: "Stage 1 — Warm",
        2: "Stage 2 — Firm",
        3: "Stage 3 — Formal",
        4: "Stage 4 — Stern",
        'legal': "Legal Flag"
    }
    return labels.get(stage, str(stage))

def get_stage_color_class(stage):
    classes = {
        1: "stage-warm",
        2: "stage-firm",
        3: "stage-formal",
        4: "stage-stern",
        'legal': "stage-legal"
    }
    return classes.get(stage, "")

invoices = load_invoices('data/invoices.csv')
invoices['stage'] = invoices['days_overdue'].apply(get_stage)
invoices['stage_label'] = invoices['stage'].apply(get_stage_label)

total = len(invoices)
legal = len(invoices[invoices['stage'] == 'legal'])
actionable = total - legal
audit_df = get_audit_log()
sent = len(audit_df[audit_df['send_status'] == 'DRY_RUN']) if not audit_df.empty else 0

st.title("Finance Credit Follow-Up Email Agent")
st.caption("Using Groq(Llama 3.3)· Dry-run mode active · No real emails sent")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Overdue", total)
col2.metric("Actionable", actionable)
col3.metric("Legal Flagged", legal, delta="Needs manual review", delta_color="inverse")
col4.metric("Emails Generated", sent)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Invoice Queue", "Email Preview", "Audit Log"])

with tab1:
    st.subheader("Invoice Queue")

    filter_stage = st.selectbox("Filter by stage", ["All", "Stage 1 — Warm", "Stage 2 — Firm", "Stage 3 — Formal", "Stage 4 — Stern", "Legal Flag"])

    display = invoices.copy()
    if filter_stage != "All":
        stage_map = {
            "Stage 1 — Warm": 1,
            "Stage 2 — Firm": 2,
            "Stage 3 — Formal": 3,
            "Stage 4 — Stern": 4,
            "Legal Flag": "legal"
        }
        display = display[display['stage'] == stage_map[filter_stage]]

    st.dataframe(
        display[['invoice_no', 'client_name', 'amount', 'due_date', 'days_overdue', 'stage_label']].rename(columns={
            'invoice_no': 'Invoice',
            'client_name': 'Client',
            'amount': 'Amount (₹)',
            'due_date': 'Due Date',
            'days_overdue': 'Days Overdue',
            'stage_label': 'Stage'
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.info("Dry-run mode is ON — no real emails will be sent. All actions are logged to the audit trail.")

    if st.button("Run Agent — Generate All Emails", type="primary"):
        init_db()
        progress = st.progress(0)
        status = st.empty()

        for i, (_, invoice) in enumerate(invoices.iterrows()):
            stage = invoice['stage']
            status.write(f"⏳ Processing {invoice['invoice_no']} — {invoice['client_name']}...")

            if stage == 'legal':
                log_entry(invoice, 'legal', 'N/A', 'FLAGGED_FOR_LEGAL')
                st.warning(f"{invoice['invoice_no']} — {invoice['client_name']}: Flagged for legal review. No email sent.")
            else:
                try:
                    subject, body = generate_email(invoice, stage)
                    log_entry(invoice, stage, subject, 'DRY_RUN')
                    st.success(f"{invoice['invoice_no']} — {invoice['client_name']} | Stage {stage} email generated")
                except Exception as e:
                    st.error(f"{invoice['invoice_no']} failed: {e}")
                    log_entry(invoice, stage, 'ERROR', 'FAILED')
                time.sleep(5)

            progress.progress((i + 1) / len(invoices))

        status.write("Agent run complete! Go to Email Preview tab to see all generated emails.")
        st.rerun()

with tab2:
    st.subheader("Generated Email Previews")
    st.caption("All emails shown below are in dry-run mode. No real emails have been sent.")

    audit_df = get_audit_log()

    if audit_df.empty or 'DRY_RUN' not in audit_df['send_status'].values:
        st.info("No emails generated yet. Go to Invoice Queue tab and run the agent first.")
    else:
        email_records = audit_df[audit_df['send_status'] == 'DRY_RUN']

        for _, record in email_records.iterrows():
            inv_row = invoices[invoices['invoice_no'] == record['invoice_no']]
            if inv_row.empty:
                continue
            inv = inv_row.iloc[0]
            stage = record['stage']
            stage_labels = {
                '1': 'Stage 1 — Warm & Friendly',
                '2': 'Stage 2 — Polite but Firm',
                '3': 'Stage 3 — Formal & Serious',
                '4': 'Stage 4 — Stern & Urgent'
            }
            stage_display = stage_labels.get(str(stage), stage)

            st.markdown(f"""
<div class="email-card">
    <div class="email-header">
        <div class="email-field">To: <span>{inv['client_name']} &lt;{inv['contact_email']}&gt;</span></div>
        <div class="email-field">Invoice: <span>{record['invoice_no']}</span> &nbsp;|&nbsp; Amount: <span>₹{int(inv['amount']):,}</span> &nbsp;|&nbsp; Overdue: <span>{record['days_overdue']} days</span></div>
        <div class="email-field">Tone: <span>{stage_display}</span></div>
        <div class="email-field">Generated: <span>{record['timestamp']}</span></div>
        <div class="email-subject"> {record['subject']}</div>
    </div>
    <div class="email-body">{record['subject'] and '' or ''}{inv['client_name'] and '' or ''}</div>
</div>
""", unsafe_allow_html=True)

            with st.expander(f" View full email body — {record['invoice_no']}"):
                st.markdown(f"**Subject:** {record['subject']}")
                st.markdown("---")
                st.text(record['subject'])

            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown('<span class="sent-badge">✓ DRY-RUN SENT</span>', unsafe_allow_html=True)
            with col2:
                st.caption(f"Logged at {record['timestamp']}")
            st.markdown("---")

with tab3:
    st.subheader("Audit Log")
    st.caption("All email addresses are masked for data privacy compliance (PII protection).")

    audit_df = get_audit_log()
    if audit_df.empty:
        st.info("No audit entries yet. Run the agent first.")
    else:
        legal_count = len(audit_df[audit_df['send_status'] == 'FLAGGED_FOR_LEGAL'])
        sent_count = len(audit_df[audit_df['send_status'] == 'DRY_RUN'])
        failed_count = len(audit_df[audit_df['send_status'] == 'FAILED'])

        c1, c2, c3 = st.columns(3)
        c1.metric("Emails Sent (Dry-run)", sent_count)
        c2.metric("Legal Flagged", legal_count)
        c3.metric("Failed", failed_count)

        st.markdown("---")

        cols_to_show = ['timestamp', 'invoice_no', 'client_name', 'amount', 'days_overdue', 'stage', 'subject', 'send_status']
        if 'contact_email_masked' in audit_df.columns:
            cols_to_show.append('contact_email_masked')

        st.dataframe(
            audit_df[cols_to_show].rename(columns={
                'timestamp': 'Timestamp',
                'invoice_no': 'Invoice',
                'client_name': 'Client',
                'amount': 'Amount (₹)',
                'days_overdue': 'Days Overdue',
                'stage': 'Stage',
                'subject': 'Subject',
                'send_status': 'Status',
                'contact_email_masked': 'Contact (Masked)'
            }),
            use_container_width=True,
            hide_index=True
        )

        if st.button("Export Audit Log as CSV"):
            csv = audit_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="audit_log.csv",
                mime="text/csv"
            )