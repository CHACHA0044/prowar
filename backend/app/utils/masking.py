"""
Privacy and Anonymization Utilities.
Ensures sensitive identifiers are masked in logs and user-facing responses.
"""


def mask_account_id(account_id: str) -> str:
    """
    Mask an account identifier for user-facing display.
    Example: 'ACC_9876543210' -> 'ACC_*****3210'
    """
    if not account_id:
        return "UNKNOWN"
    if len(account_id) <= 6:
        return f"{account_id[:2]}***"
    return f"{account_id[:4]}***{account_id[-4:]}"

