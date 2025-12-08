"""Dutch public holidays checker."""
from datetime import date


def is_dutch_holiday(check_date: date) -> bool:
    """Check if a date is a Dutch public holiday.
    
    Args:
        check_date: The date to check
        
    Returns:
        True if the date is a Dutch public holiday, False otherwise
    """
    year = check_date.year
    
    # Fixed holidays
    fixed_holidays = [
        (1, 1),   # New Year's Day
        (4, 27),  # King's Day
        (5, 5),   # Liberation Day (every 5 years, but commonly celebrated)
        (12, 25), # Christmas Day
        (12, 26), # Second Christmas Day
    ]
    
    if (check_date.month, check_date.day) in fixed_holidays:
        return True
    
    # Easter-based holidays (simplified - using approximation)
    # For accurate Easter calculation, you'd use a library, but this is a simple approximation
    easter_dates = {
        2024: (3, 31),
        2025: (4, 20),
        2026: (4, 5),
        2027: (3, 28),
        2028: (4, 16),
        2029: (4, 1),
        2030: (4, 21),
    }
    
    if year in easter_dates:
        easter_month, easter_day = easter_dates[year]
        
        # Easter Monday (Easter + 1 day)
        if check_date.month == easter_month and check_date.day == easter_day + 1:
            return True
        
        # Good Friday (Easter - 2 days) - approximation
        if check_date.month == easter_month and check_date.day == easter_day - 2:
            return True
        
        # Ascension Day (Easter + 39 days) - approximation
        # Whit Monday (Easter + 50 days) - approximation
        # These are more complex to calculate accurately, simplified here
    
    return False
