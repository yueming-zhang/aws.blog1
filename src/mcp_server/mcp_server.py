from mcp.server.fastmcp import FastMCP
from tracing_utils import traced, traced_async
import logging
import sys
import time
import asyncio
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

SERVER_INSTANCE_ID = str(uuid.uuid4())

mcp = FastMCP(host="0.0.0.0", stateless_http=True)


@mcp.tool()
def add_numbers_sync(a: int, b: int) -> str:
    """Add two numbers together (sync)"""
    logger.info(f"Adding numbers (sync): {a} + {b}")
    result = a + b
    time.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


@mcp.tool()
async def add_numbers_async(a: int, b: int) -> str:
    """Add two numbers together (async)"""
    logger.info(f"Adding numbers (async): {a} + {b}")
    result = a + b
    await asyncio.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


@mcp.tool()
@traced(
    span_name="tool.multiply_numbers_sync",
    attributes={"tool.name": "multiply_numbers_sync", "service": "mcp_server"},
)
def multiply_numbers_sync(a: int, b: int) -> str:
    """Multiply two numbers together (sync)"""
    logger.info(f"Multiplying numbers (sync): {a} * {b}")
    result = a * b
    time.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


@mcp.tool()
@traced_async(
    span_name="tool.multiply_numbers_async",
    attributes={"tool.name": "multiply_numbers_async", "service": "mcp_server"},
)
async def multiply_numbers_async(a: int, b: int) -> str:
    """Multiply two numbers together (async)"""
    logger.info(f"Multiplying numbers (async): {a} * {b}")
    result = a * b
    await asyncio.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


@mcp.tool()
@traced(
    span_name="tool.greet_user",
    attributes={"tool.name": "greet_user", "service": "mcp_server"},
)
def greet_user(name: str) -> str:
    """Greet a user by name"""
    logger.info(f"Greeting user: {name}")
    greeting = f"Hello, {name}! Nice to meet you here again."
    time.sleep(2)
    return f"result={greeting} server={SERVER_INSTANCE_ID}"


if __name__ == "__main__":
    logger.info("Starting MCP server with tracing enabled...")
    mcp.run(transport="streamable-http")
