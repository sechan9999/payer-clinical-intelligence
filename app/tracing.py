import functools
import logging
from typing import Any, Callable
from opentelemetry import trace

logger = logging.getLogger("payer_clinical_governance")
tracer = trace.get_tracer("payer_clinical_agents", "0.1.0")


def governed_span(action_name: str):
    """
    Decorator for attaching OpenTelemetry governance attributes to execution spans.
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
                    span.set_attribute("governance.status", "SUCCESS")
                    return result
                except Exception as ex:
                    span.set_attribute("governance.status", "ERROR")
                    span.set_attribute("governance.error_detail", str(ex))
                    raise ex
        return wrapper
    return decorator
