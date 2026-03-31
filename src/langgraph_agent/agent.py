import os
import uuid

import boto3
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from bedrock_agentcore import BedrockAgentCoreApp

from streamable_http_sigv4 import streamablehttp_client_with_sigv4

SERVER_INSTANCE_ID = str(uuid.uuid4())

app = BedrockAgentCoreApp()

REGION = os.environ.get("AWS_REGION", "us-west-2")
MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
llm = ChatBedrock(model_id=MODEL_ID, region_name=REGION)

# MCP server ARN — hardcoded to avoid needing SSM permissions on the execution role
MCP_AGENT_ARN = "arn:aws:bedrock-agentcore:us-west-2:980413094772:runtime/blog_mcp_math-Z057Lr3Pdg"
_encoded_arn = MCP_AGENT_ARN.replace(":", "%3A").replace("/", "%2F")
MCP_URL = f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{_encoded_arn}/invocations?qualifier=DEFAULT"


def create_transport():
    session = boto3.Session()
    credentials = session.get_credentials()
    return streamablehttp_client_with_sigv4(
        url=MCP_URL,
        credentials=credentials,
        service="bedrock-agentcore",
        region=REGION,
    )


@app.entrypoint
async def invoke(payload, context):
    """
    HTTP entrypoint for the LangGraph agent.

    Connects to the AgentCore-hosted MCP server, loads its tools,
    and runs a ReAct agent that uses those tools.

    Expected payload: {"prompt": "add 3 and 5"}
    Returns: {"result": "<tool output>", "server": "<agent instance id>"}
    """
    prompt = payload.get("prompt", "add 1 and 2")

    async with create_transport() as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as mcp_session:
            await mcp_session.initialize()

            # Load MCP tools as LangChain tools, filter to async only
            all_tools = await load_mcp_tools(mcp_session)
            async_tools = [t for t in all_tools if "async" in t.name]

            graph = create_react_agent(
                llm,
                tools=async_tools,
                prompt=SystemMessage(
                    content=(
                        "You are a math assistant. Use the provided tools to perform calculations. "
                        "Always use the tool — never compute the answer yourself. "
                        "Return the tool output verbatim as your final answer."
                    )
                ),
            )

            result = await graph.ainvoke({"messages": [HumanMessage(content=prompt)]})

    # Extract tool output directly from message history
    # MCP adapter returns content as list of dicts: [{'type': 'text', 'text': '...'}]
    tool_output = None
    for msg in reversed(result["messages"]):
        if isinstance(msg, ToolMessage):
            content = msg.content
            if isinstance(content, list):
                tool_output = " ".join(block["text"] for block in content if block.get("type") == "text")
            else:
                tool_output = content
            break

    return {
        "result": tool_output or result["messages"][-1].content,
        "server": SERVER_INSTANCE_ID,
        "session_id": context.session_id,
    }


if __name__ == "__main__":
    print(f"LangGraph agent starting — instance {SERVER_INSTANCE_ID}")
    app.run()
