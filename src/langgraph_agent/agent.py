import uuid
import time
import asyncio

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from bedrock_agentcore import BedrockAgentCoreApp

SERVER_INSTANCE_ID = str(uuid.uuid4())

app = BedrockAgentCoreApp()

# --- Tools (mirrors MCP server math tools) ---


@tool
def add_numbers_sync(a: int, b: int) -> str:
    """Add two numbers together (sync)"""
    print(f"Adding numbers (sync): {a} + {b}")
    result = a + b
    time.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


@tool
async def add_numbers_async(a: int, b: int) -> str:
    """Add two numbers together (async)"""
    print(f"Adding numbers (async): {a} + {b}")
    result = a + b
    await asyncio.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


@tool
def multiply_numbers_sync(a: int, b: int) -> str:
    """Multiply two numbers together (sync)"""
    print(f"Multiplying numbers (sync): {a} * {b}")
    result = a * b
    time.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


@tool
async def multiply_numbers_async(a: int, b: int) -> str:
    """Multiply two numbers together (async)"""
    print(f"Multiplying numbers (async): {a} * {b}")
    result = a * b
    await asyncio.sleep(2)
    return f"result={result} server={SERVER_INSTANCE_ID}"


# --- LangGraph Agent ---

MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"

llm = ChatBedrock(model_id=MODEL_ID, region_name="us-west-2")

tools = [add_numbers_sync, add_numbers_async, multiply_numbers_sync, multiply_numbers_async]

graph = create_react_agent(
    llm,
    tools=tools,
    prompt=SystemMessage(
        content=(
            "You are a math assistant. Use the provided tools to perform calculations. "
            "Always use the tool — never compute the answer yourself. "
            "Return the tool output verbatim as your final answer."
        )
    ),
)


@app.entrypoint
async def invoke(payload, context):
    """
    HTTP entrypoint for the LangGraph agent.

    Expected payload: {"prompt": "add 3 and 5", "tool_mode": "sync"|"async"}
    Returns: {"result": "<tool output>", "server": "<instance id>"}
    """
    prompt = payload.get("prompt", "add 1 and 2")
    tool_mode = payload.get("tool_mode", "async")

    # Hint the LLM which tool variant to use
    mode_hint = f" Use the {tool_mode} version of the tool."
    full_prompt = prompt + mode_hint

    result = await graph.ainvoke({"messages": [HumanMessage(content=full_prompt)]})

    # Extract the tool output directly from message history instead of
    # relying on the LLM's final answer (which is non-deterministic)
    tool_output = None
    for msg in reversed(result["messages"]):
        if isinstance(msg, ToolMessage):
            tool_output = msg.content
            break

    return {
        "result": tool_output or result["messages"][-1].content,
        "server": SERVER_INSTANCE_ID,
        "session_id": context.session_id,
    }


if __name__ == "__main__":
    print(f"LangGraph agent starting — instance {SERVER_INSTANCE_ID}")
    app.run()
