import functools
import logging
import re
from typing import Any, Callable
from opentelemetry import trace

logger = logging.getLogger("payer_clinical_governance")
tracer = trace.get_tracer("payer_clinical_agents", "0.1.0")


def redact_url_credentials(text: str) -> str:
    """
    Redacts DB passwords and credentials from connection strings and URLs in logs.
    Prevents credential leaks in Cloud Logging traces.
    """
    if not text:
        return ""
    # Pattern matching :password@ in URLs
    return re.sub(r":([^/@:]+)@", ":***@", text)


def governed_span(action_name: str):
    """
    Decorator for attaching OpenTelemetry governance attributes to execution spans.
    Sets 'fleet.access_denied = True' on refusals so denials are first-class in Cloud Trace.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with tracer.start_as_current_span(action_name) as span:
                span.set_attribute("governance.action", action_name)
                # Extract identity if available in kwargs
                identity = kwargs.get("user_identity")
                if identity:
                    span.set_attribute("governance.user_id", identity.user_id)
                    span.set_attribute("governance.user_role", identity.role.value)
                    span.set_attribute("governance.department", identity.department)

                try:
                    result = func(*args, **kwargs)
                    
                    # Check if result indicates access denial
                    if isinstance(result, dict):
                        if not result.get("success", True) or result.get("status") == "DENIED":
                            span.set_attribute("fleet.access_denied", True)
                            span.set_attribute("governance.status", "REFUSED")
                        else:
                            span.set_attribute("fleet.access_denied", False)
                            span.set_attribute("governance.status", "SUCCESS")
                    else:
                        span.set_attribute("fleet.access_denied", False)
                        span.set_attribute("governance.status", "SUCCESS")

                    return result
                except Exception as ex:
                    span.set_attribute("fleet.access_denied", True)
                    span.set_attribute("governance.status", "ERROR")
                    clean_msg = redact_url_credentials(str(ex))
                    span.set_attribute("governance.error_detail", clean_msg)
                    logger.error(f"Error in {action_name}: {type(ex).__name__}")
                    raise ex
        return wrapper
    return decorator
