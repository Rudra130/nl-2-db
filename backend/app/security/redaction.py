"""Secret and Credential Redaction Module."""
import re
from typing import Any

# Patterns matching sensitive parameters and secrets
SENSITIVE_PATTERNS = [
    re.compile(r"(api[_-]?key|password|secret|token|bearer|auth|nvapi)[\s:=]+([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(nvapi-[A-Za-z0-9_-]{20,})", re.IGNORECASE),
    re.compile(r"(mysql|postgresql|postgres|mongodb)(\+[^:]+)?://([^:]+):([^@]+)@", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Redact passwords, connection string credentials, and API keys from text."""
    if not isinstance(text, str):
        return str(text)

    redacted = text
    # Redact connection URIs
    redacted = re.sub(
        r"(mysql|postgresql|postgres|mongodb)(\+[^:]+)?://([^:]+):([^@]+)@",
        r"\1\2://\3:***REDACTED***@",
        redacted,
    )
    # Redact NVAPI keys
    redacted = re.sub(r"(nvapi-[A-Za-z0-9_-]{6})[A-Za-z0-9_-]+", r"\1...[REDACTED]", redacted)
    # Redact key/password fields
    redacted = re.sub(
        r'(?i)("?(?:password|token|secret|apiKey|api_key)"?\s*[:=]\s*["\'])([^"\']+)(["\'])',
        r"\1***REDACTED***\3",
        redacted,
    )
    return redacted


def sanitize_error_message(error: Exception | str) -> str:
    """Sanitize database or system exception message before exposing to user/LLM."""
    err_str = str(error)
    # Never expose path names, internal IPs or credentials
    sanitized = redact_secrets(err_str)
    # Strip local file paths if present
    sanitized = re.sub(r"[A-Za-z]:\\[^:\n\r]+", "[FILE_PATH]", sanitized)
    sanitized = re.sub(r"/home/[^:\n\r]+", "[FILE_PATH]", sanitized)
    return sanitized
