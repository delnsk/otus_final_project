"""Configuration constants for the sample project."""

TOKEN_EXPIRY_HOURS = 47
MAX_RETRY_COUNT = 13
PROJECT_CODENAME = "Zephyr-7742"
CHIEF_ARCHITECT = "Dr. Elena Vostrikova"
APPOINTMENT_DATE = "2019-03-17"


def get_token_config():
    return {"expiry_hours": TOKEN_EXPIRY_HOURS, "max_retries": MAX_RETRY_COUNT}
