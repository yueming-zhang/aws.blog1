"""
Reusable tracing utilities for AgentCore applications.
Provides decorators to automatically instrument functions with OpenTelemetry spans.
"""

from functools import wraps
from typing import Callable, Any, Optional
from opentelemetry import trace
import logging
import inspect
import time

logger = logging.getLogger(__name__)


def traced(
    span_name: Optional[str] = None,
    attributes: Optional[dict] = None,
    capture_args: bool = True,
    capture_result: bool = True,
    capture_exceptions: bool = True
):
    """
    Decorator to automatically add OpenTelemetry span instrumentation to any function.
    
    Args:
        span_name: Custom span name (defaults to function name)
        attributes: Static attributes to add to the span
        capture_args: Whether to capture function arguments as span attributes
        capture_result: Whether to capture return value as span attribute
        capture_exceptions: Whether to record exceptions in the span
    
    Example:
        @traced()
        def my_function(x: int, y: str) -> dict:
            return {"result": x}
        
        @traced(span_name="custom_operation", attributes={"service": "weather"})
        def fetch_data(location: str) -> str:
            return f"Data for {location}"
        
        @traced(capture_args=False, capture_result=False)
        def sensitive_operation(api_key: str) -> dict:
            # Won't capture api_key or result in span
            return {"status": "ok"}
    """
    def decorator(func: Callable) -> Callable:
        # Get tracer for this module
        tracer = trace.get_tracer(func.__module__)
        
        # Determine span name
        operation_name = span_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Start span
            with tracer.start_as_current_span(operation_name) as span:
                start_time = time.perf_counter()
                try:
                    # Add static attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Capture arguments if enabled
                    if capture_args:
                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()
                        
                        for param_name, param_value in bound_args.arguments.items():
                            # Convert to string and truncate if too long
                            value_str = str(param_value)
                            if len(value_str) > 200:
                                value_str = value_str[:200] + "..."
                            span.set_attribute(f"arg.{param_name}", value_str)
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Capture duration
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", round(duration_ms, 2))
                    
                    # Capture result if enabled
                    if capture_result:
                        result_str = str(result)
                        if len(result_str) > 200:
                            result_str = result_str[:200] + "..."
                        span.set_attribute("result.value", result_str)
                        span.set_attribute("result.type", type(result).__name__)
                    
                    # Mark as successful
                    span.set_attribute("status", "success")
                    
                    return result
                    
                except Exception as e:
                    # Capture duration even on error
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", round(duration_ms, 2))
                    
                    # Record exception if enabled
                    if capture_exceptions:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    
                    # Re-raise the exception
                    raise
        
        return wrapper
    return decorator


def traced_async(
    span_name: Optional[str] = None,
    attributes: Optional[dict] = None,
    capture_args: bool = True,
    capture_result: bool = True,
    capture_exceptions: bool = True
):
    """
    Async version of @traced decorator for async functions.
    
    Example:
        @traced_async()
        async def fetch_data_async(location: str) -> dict:
            await asyncio.sleep(1)
            return {"location": location}
    """
    def decorator(func: Callable) -> Callable:
        tracer = trace.get_tracer(func.__module__)
        operation_name = span_name or func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            with tracer.start_as_current_span(operation_name) as span:
                start_time = time.perf_counter()
                try:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    if capture_args:
                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()
                        
                        for param_name, param_value in bound_args.arguments.items():
                            value_str = str(param_value)
                            if len(value_str) > 200:
                                value_str = value_str[:200] + "..."
                            span.set_attribute(f"arg.{param_name}", value_str)
                    
                    result = await func(*args, **kwargs)
                    
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", round(duration_ms, 2))
                    
                    if capture_result:
                        result_str = str(result)
                        if len(result_str) > 200:
                            result_str = result_str[:200] + "..."
                        span.set_attribute("result.value", result_str)
                        span.set_attribute("result.type", type(result).__name__)
                    
                    span.set_attribute("status", "success")
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", round(duration_ms, 2))
                    
                    if capture_exceptions:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    
                    raise
        
        return wrapper
    return decorator


class SpanContext:
    """
    Context manager for creating spans with automatic attribute management.
    
    Example:
        with SpanContext("database_query") as span_ctx:
            span_ctx.add("query.table", "users")
            span_ctx.add("query.limit", 100)
            result = execute_query()
            span_ctx.add("result.count", len(result))
    """
    def __init__(self, span_name: str, tracer: Optional[trace.Tracer] = None):
        self.span_name = span_name
        self.tracer = tracer or trace.get_tracer(__name__)
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_as_current_span(self.span_name).__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.record_exception(exc_val)
            self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        self.span.__exit__(exc_type, exc_val, exc_tb)
    
    def add(self, key: str, value: Any):
        """Add an attribute to the current span."""
        if self.span:
            self.span.set_attribute(key, value)
    
    def add_event(self, name: str, attributes: Optional[dict] = None):
        """Add an event to the current span."""
        if self.span:
            self.span.add_event(name, attributes or {})


def trace_class_methods(
    exclude: Optional[list] = None,
    include_private: bool = False
):
    """
    Class decorator to automatically trace all methods in a class.
    
    Args:
        exclude: List of method names to exclude from tracing
        include_private: Whether to trace private methods (starting with _)
    
    Example:
        @trace_class_methods(exclude=["__init__", "_internal_helper"])
        class WeatherService:
            def fetch_weather(self, location: str) -> dict:
                return {"temp": 72}
            
            def process_data(self, data: dict) -> dict:
                return data
    """
    exclude = exclude or []
    
    def decorator(cls):
        for attr_name in dir(cls):
            # Skip excluded methods
            if attr_name in exclude:
                continue
            
            # Skip private methods unless explicitly included
            if attr_name.startswith("_") and not include_private:
                continue
            
            # Skip special methods
            if attr_name.startswith("__") and attr_name.endswith("__"):
                continue
            
            attr = getattr(cls, attr_name)
            
            # Only trace callable methods
            if callable(attr):
                # Apply traced decorator
                traced_method = traced(
                    span_name=f"{cls.__name__}.{attr_name}"
                )(attr)
                setattr(cls, attr_name, traced_method)
        
        return cls
    
    return decorator


# Convenience function for manual span creation
def create_span(name: str, attributes: Optional[dict] = None):
    """
    Create a span context manager for manual instrumentation.
    
    Example:
        with create_span("my_operation", {"key": "value"}) as span:
            # Your code here
            span.set_attribute("result", "success")
    """
    tracer = trace.get_tracer(__name__)
    span = tracer.start_as_current_span(name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span
