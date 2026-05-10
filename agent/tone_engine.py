TONE_MATRIX = {
    1: {
        "stage_name": "1st Follow-Up",
        "trigger": "1-7 days overdue",
        "tone": "Warm & Friendly",
        "cta": "Pay now link / bank details",
        "system_prompt": (
            "You are a professional accounts receivable assistant. "
            "Write a warm and friendly payment reminder email. "
            "Be polite, assume the delay was an oversight. "
            "Never sound threatening or urgent."
        )
    },
    2: {
        "stage_name": "2nd Follow-Up",
        "trigger": "8-14 days overdue",
        "tone": "Polite but Firm",
        "cta": "Confirm payment date",
        "system_prompt": (
            "You are a professional accounts receivable assistant. "
            "Write a polite but firm payment reminder email. "
            "The client has missed the deadline. "
            "Request a confirmation of payment date."
        )
    },
    3: {
        "stage_name": "3rd Follow-Up",
        "trigger": "15-21 days overdue",
        "tone": "Formal & Serious",
        "cta": "Respond within 48 hours",
        "system_prompt": (
            "You are a professional accounts receivable assistant. "
            "Write a formal and serious payment reminder email. "
            "Express escalating concern. "
            "Mention that continued non-payment may impact credit terms. "
            "Ask them to respond within 48 hours."
        )
    },
    4: {
        "stage_name": "4th Follow-Up",
        "trigger": "22-30 days overdue",
        "tone": "Stern & Urgent",
        "cta": "Pay immediately or call us",
        "system_prompt": (
            "You are a professional accounts receivable assistant. "
            "Write a stern and urgent final reminder email. "
            "Make clear this is the last notice before escalation "
            "to the legal and recovery team. "
            "Demand immediate payment within 24 hours."
        )
    },
    "legal": {
        "stage_name": "Escalation Flag",
        "trigger": "30+ days overdue",
        "tone": "No email — Flag for Legal",
        "cta": "Assign to finance manager",
        "system_prompt": None
    }
}

def get_tone(stage):
    return TONE_MATRIX.get(stage)