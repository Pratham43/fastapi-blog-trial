import logging
import re
import sys
from typing import Any
import structlog
from app.config import settings

# Redact sensitive information (PII) from logs before writing/emitting
PII_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "***@***.***"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "***-***-****"),
    (re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"), "****-****-****-****"),
    (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9._~+/=-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(password|secret|token|api_key)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
]

def mask_pii(_logger: Any, _method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Structlog processor to mask PII in log events."""
    event = event_dict.get("event", "")
    if isinstance(event, str):
        for pattern, replacement in PII_PATTERNS:
            event = pattern.sub(replacement, event)
        event_dict["event"] = event

    for key, value in event_dict.items():
        if isinstance(value, str) and key not in ("event", "timestamp", "level"):
            for pattern, replacement in PII_PATTERNS:
                value = pattern.sub(replacement, value)
            event_dict[key] = value
    return event_dict

def setup_logging() -> None:
    """Configure structlog and bind it to standard logging."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        mask_pii,
    ]

    if settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Prevent duplicates and suppress noise from framework loggers
    for noisy_logger in ("uvicorn.access", "sqlalchemy.engine", "aiosmtplib"):
        logger = logging.getLogger(noisy_logger)
        logger.handlers.clear()
        logger.propagate = False
        logger.setLevel(logging.WARNING)

    structlog.get_logger().info(
        "Structured logging initialized",
        level=settings.log_level,
        format=settings.log_format,
    )

def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Retrieve a structured logger instance."""
    return structlog.get_logger(name)
