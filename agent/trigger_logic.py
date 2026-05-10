def get_stage(days_overdue):
    if days_overdue > 30:
        return 'legal'
    elif days_overdue >= 22:
        return 4
    elif days_overdue >= 15:
        return 3
    elif days_overdue >= 8:
        return 2
    else:
        return 1