from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from opentelemetry import trace
import time
import asyncio


mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    print(f"Adding numbers: {a} + {b}")
    """Add two numbers together"""
    tracer = trace.get_tracer("math_mcp", "1.0.0")
    with tracer.start_as_current_span("math_mcp_add_numbers") as span:
        span.add_event("add_numbers_start", {"a": a, "b": b})
        result = a + b
        time.sleep(2)        
        span.add_event("add_numbers_end", {"result": result})
        span.set_status(trace.Status(trace.StatusCode.OK))

    return result

@mcp.tool()
async def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together"""
    print(f"Multiplying numbers: {a} * {b}")
    tracer = trace.get_tracer("math_mcp", "1.0.0")
    with tracer.start_as_current_span("math_mcp_multiply_numbers") as span:
        span.add_event("multiply_numbers_start", {"a": a, "b": b})
        result = a * b
        await asyncio.sleep(2)
        span.add_event("multiply_numbers_end", {"result": result})
        span.set_status(trace.Status(trace.StatusCode.OK))        
    return result

@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user by name"""
    print(f"Greeting user: {name}")
    tracer = trace.get_tracer("greet_mcp", "1.0.0")
    with tracer.start_as_current_span("greet_mcp_user") as span:
        span.add_event("greet_user_start", {"name": name})
        greeting = f"Hello, {name}! Nice to meet you here again."
        time.sleep(2)
        span.add_event("greet_user_end", {"greeting": greeting})
        span.set_status(trace.Status(trace.StatusCode.OK))
    return greeting

if __name__ == "__main__":
    print("MCP initialization : true cold cold start")
    mcp.run(transport="streamable-http")
