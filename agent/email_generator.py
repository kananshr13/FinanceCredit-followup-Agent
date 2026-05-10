from groq import Groq
import os
import json
import re
from dotenv import load_dotenv
from agent.tone_engine import get_tone

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def sanitise_input(value):
    value = str(value)
    value = re.sub(r'[<>{}[\]\\]', '', value)
    value = value.replace('ignore previous instructions', '')
    value = value.replace('system:', '')
    value = value.replace('user:', '')
    return value.strip()

def generate_email(invoice, stage):
    tone = get_tone(stage)
    system_prompt = tone['system_prompt']

    client_name = sanitise_input(invoice['client_name'])
    invoice_no = sanitise_input(invoice['invoice_no'])
    amount = sanitise_input(invoice['amount'])
    due_date = invoice['due_date'].strftime('%d %b %Y')
    days_overdue = sanitise_input(invoice['days_overdue'])
    followup_count = sanitise_input(invoice['followup_count'])

    user_prompt = f"""
Generate a payment follow-up email using the details below.
Return ONLY a JSON object with two keys: "subject" and "body". No extra text, no markdown.

Client Name: {client_name}
Invoice Number: {invoice_no}
Amount Due: Rs.{int(float(amount)):,}
Due Date: {due_date}
Days Overdue: {days_overdue}
Payment Link: https://pay.example.com/{invoice_no}
Follow-up Count: {followup_count}
Tone: {tone['tone']}
Call To Action: {tone['cta']}

Tone instruction: {system_prompt}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    return result['subject'], result['body']