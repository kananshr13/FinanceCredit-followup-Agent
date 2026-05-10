# Finance Credit Follow-Up Email Agent

An AI-powered agent that automates payment follow-up emails for overdue invoices. The agent reads pending credit records, determines the appropriate escalation stage based on how overdue each invoice is, generates a personalised email using a large language model, and logs every action to an audit trail. No real emails are sent during testing — the agent runs in dry-run mode.

This project was built as part of the AI Enablement Internship assignment.

---

## What the Agent Does

Finance teams spend significant time chasing overdue payments manually. This agent automates that workflow by:

- Reading invoice data from a CSV file
- Calculating how many days each invoice is overdue
- Assigning the correct escalation stage based on days overdue
- Generating a personalised, professional email at the right tone for that stage
- Logging every generated email to a SQLite audit trail with masked contact details
- Flagging invoices overdue by more than 30 days for legal review instead of sending an email
- Displaying everything through a Streamlit dashboard

---

## Tone Escalation Matrix

| Stage | Trigger | Tone | Call to Action |
|---|---|---|---|
| Stage 1 | 1-7 days overdue | Warm and Friendly | Pay now link |
| Stage 2 | 8-14 days overdue | Polite but Firm | Confirm payment date |
| Stage 3 | 15-21 days overdue | Formal and Serious | Respond within 48 hours |
| Stage 4 | 22-30 days overdue | Stern and Urgent | Pay immediately or call |
| Legal Flag | 30+ days overdue | No email sent | Assigned to finance manager |

---

## Agent Architecture

```
invoices.csv
     |
     v
ingestor.py
Reads CSV file, parses due dates, calculates days overdue for each invoice

     |
     v
trigger_logic.py
Determines escalation stage based on days overdue
(Stage 1 / Stage 2 / Stage 3 / Stage 4 / Legal Flag)

     |
     v
tone_engine.py
Provides tone label, call to action, and system prompt for the assigned stage

     |
     v
email_generator.py
Sanitises input, builds prompt, calls Gemini 2.0 Flash API
Returns structured JSON with subject and body

     |
     v
audit_logger.py
Logs invoice details, stage, subject, send status, and masked email to SQLite

     |
     v
app.py
Streamlit dashboard — Invoice Queue, Email Preview, Audit Log
```

## Tech Stack and Decision Log

### LLM — Groq API with Llama 3.3 70B

Model chosen: llama-3.3-70b-versatile via the Groq Python SDK.

Groq was selected over alternatives for the following reasons:

- It provides a completely free API with no credit card required
- It has significantly higher rate limits than the Gemini free tier
- Llama 3.3 70B is a highly capable open-source model with strong 
  instruction-following and JSON output reliability
- The Groq inference engine is extremely fast compared to other providers
- GPT-4o and Claude Sonnet were considered but both require paid API 
  access from the start
- Gemini 2.0 Flash was tested but its free tier daily quota was too 
  restrictive for running the agent across multiple invoices
- Llama 3 local was ruled out because it requires downloading 
  multi-gigabyte model files which cannot be version-controlled on GitHub

### Agent Framework — Direct API calls with modular Python

LangChain and CrewAI were considered but not used for this prototype. The task involves a linear, single-agent workflow: ingest, classify, generate, log. Introducing a framework like LangChain would add unnecessary complexity and dependencies without meaningful benefit at this scale.

The agent is structured as a pipeline of single-responsibility modules, each with a clearly defined input and output. This makes the code easier to read, test, and extend.

If this were scaled to a multi-agent system — for example, a separate agent for scheduling, one for send decisions, and one for escalation routing — LangChain or LangGraph would be the natural next step.

### Prompt Design

Each escalation stage has a dedicated system prompt stored in tone_engine.py. The prompts are kept short and specific to avoid hallucination and keep token usage low.

The user prompt injects all invoice fields directly: client name, invoice number, amount, due date, days overdue, payment link, follow-up count, tone label, and call to action. The LLM is instructed to return only a JSON object with two keys — subject and body — with no additional text or markdown formatting.

This structured output approach means the response can be parsed reliably without brittle string manipulation.

Prompt iteration notes:

- Early versions asked the LLM to write the email directly as plain text. This made parsing unreliable when the model added preamble or sign-off text outside the email body
- Switching to JSON mode resolved this immediately
- The instruction "No extra text, no markdown" was added after observing the model occasionally wrapping the JSON in code fences

---

## Security Mitigations

### API Key Exposure

The Gemini API key is stored in a .env file and loaded via python-dotenv. It is never hardcoded in any source file. The .env file is listed in .gitignore and will never be committed to the repository. A .env.example file is provided with a placeholder value so other developers know what to set up.

### Prompt Injection

All invoice field values are passed through a sanitise_input() function in email_generator.py before being injected into the prompt. This function strips characters commonly used in injection attacks and removes phrases like "ignore previous instructions" that could attempt to override the agent's behaviour. Structured JSON output further limits the blast radius of any injection attempt since the model is constrained to return a specific schema.

### Data Privacy and PII

Invoice data contains personal information including client names and email addresses. Email addresses are masked before being written to the audit log — for example, rajesh@kapoor.in becomes r***@kapoor.in. The raw email address is used only at the point of generation and is never persisted in plaintext to any log or database.

### Hallucination Risk

The LLM is instructed to return only a JSON object with predefined keys. The response is parsed with json.loads() inside a try/except block. If the model returns malformed output, the error is caught, logged to the audit trail with status FAILED, and the agent continues processing the remaining invoices. This prevents a single hallucinated response from crashing the entire run.

### Unauthorised Access

In the current prototype, the Streamlit dashboard runs locally and is not exposed to the internet. For a production deployment, the recommended approach is to add OAuth authentication or an API key check at the application layer and enable rate limiting on any exposed endpoint.

### Email Spoofing

The agent runs in dry-run mode during development and testing. No emails are dispatched to real addresses. For a production deployment with real sending, SPF, DKIM, and DMARC records should be configured on the sender domain, and a verified sender identity should be set up through the chosen email provider such as SendGrid or Mailgun.

---

## Project Structure

credit-followup-agent/
├── agent/
│   ├── init.py
│   ├── ingestor.py
│   ├── trigger_logic.py
│   ├── tone_engine.py
│   ├── email_generator.py
│   └── audit_logger.py
├── data/
│   └── invoices.csv
├── logs/
│   └── audit.db
├── app.py
├── main.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

---

## Setup Instructions

### 1. Clone the repository
### 2. Install dependencies
### 3. Add your API key
### 4. Run the Streamlit dashboard
### 5. Or run the agent from the terminal
---

## Sample Output

A sample audit log CSV is included in the repository under logs/sample_output.csv showing generated emails across all four escalation stages.

---

## Limitations and Future Improvements

- The free tier of Gemini 2.0 Flash has a daily request quota. For production use, a paid tier or request caching via LangChain SQLite cache would be appropriate
- Real email sending via SendGrid or Mailgun would replace the current dry-run mode
- A scheduling layer using APScheduler or GitHub Actions cron could run the agent automatically every morning
- LangSmith or Langfuse tracing could be added for observability and prompt debugging

