"""Integration tests for the math MCP server deployed on AWS AgentCore.

Requires a live deployment. The agent ARN is resolved from (in order):
    1. AGENT_ARN environment variable
    2. SSM parameter named by SSM_PARAM_AGENT_ARN (default: /math-mcp/dev/agent_arn)

Run with:
    uv run pytest tests/integration/ -v -m integration
"""

import asyncio
import os

import boto3
import pytest
from mcp import ClientSession

from utils.sigv4_auth import streamablehttp_client_with_sigv4


def _resolve_agent_arn(region: str) -> str:
    agent_arn = os.environ.get("AGENT_ARN")
    if agent_arn:
        return agent_arn
    ssm_param = os.environ.get("SSM_PARAM_AGENT_ARN", "/math-mcp/dev/agent_arn")
    ssm = boto3.client("ssm", region_name=region)
    return ssm.get_parameter(Name=ssm_param)["Parameter"]["Value"]


def _build_mcp_url(agent_arn: str, region: str) -> str:
    encoded = agent_arn.replace(":", "%3A").replace("/", "%2F")
    return (
        f"https://bedrock-agentcore.{region}.amazonaws.com"
        f"/runtimes/{encoded}/invocations?qualifier=DEFAULT"
    )


@pytest.fixture(scope="module")
def mcp_config():
    session = boto3.Session()
    region = os.environ.get("AWS_REGION") or session.region_name or "us-west-2"
    agent_arn = _resolve_agent_arn(region)
    return {
        "url": _build_mcp_url(agent_arn, region),
        "credentials": session.get_credentials(),
        "region": region,
    }


async def _call_tool(config: dict, tool_name: str, arguments: dict):
    async with streamablehttp_client_with_sigv4(
        url=config["url"],
        credentials=config["credentials"],
        service="bedrock-agentcore",
        region=config["region"],
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            return await session.call_tool(name=tool_name, arguments=arguments)


@pytest.mark.integration
class TestMathMCPIntegration:
    def test_list_tools(self, mcp_config):
        async def _run():
            async with streamablehttp_client_with_sigv4(
                url=mcp_config["url"],
                credentials=mcp_config["credentials"],
                service="bedrock-agentcore",
                region=mcp_config["region"],
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await session.list_tools()

        result = asyncio.run(_run())
        tool_names = {t.name for t in result.tools}
        assert tool_names == {"add", "subtract", "multiply", "divide"}

    def test_add(self, mcp_config):
        result = asyncio.run(_call_tool(mcp_config, "add", {"a": 10, "b": 5}))
        assert not result.isError
        assert float(result.content[0].text) == 15.0

    def test_subtract(self, mcp_config):
        result = asyncio.run(_call_tool(mcp_config, "subtract", {"a": 10, "b": 5}))
        assert not result.isError
        assert float(result.content[0].text) == 5.0

    def test_multiply(self, mcp_config):
        result = asyncio.run(_call_tool(mcp_config, "multiply", {"a": 4, "b": 7}))
        assert not result.isError
        assert float(result.content[0].text) == 28.0

    def test_divide(self, mcp_config):
        result = asyncio.run(_call_tool(mcp_config, "divide", {"a": 20, "b": 4}))
        assert not result.isError
        assert float(result.content[0].text) == 5.0

    def test_divide_by_zero(self, mcp_config):
        result = asyncio.run(_call_tool(mcp_config, "divide", {"a": 1, "b": 0}))
        assert result.isError
        assert "zero" in result.content[0].text.lower()

    def test_float_inputs(self, mcp_config):
        result = asyncio.run(_call_tool(mcp_config, "add", {"a": 1.5, "b": 2.5}))
        assert not result.isError
        assert float(result.content[0].text) == 4.0
