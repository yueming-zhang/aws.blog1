import logging

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

mcp = FastMCP(host="0.0.0.0", stateless_http=True)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    logger.info("add(%s, %s)", a, b)
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    logger.info("subtract(%s, %s)", a, b)
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    logger.info("multiply(%s, %s)", a, b)
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises ValueError if b is zero."""
    logger.info("divide(%s, %s)", a, b)
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
