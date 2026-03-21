import pytest
import boto3
from boto3.session import Session
from mcp import ClientSession
from streamable_http_sigv4 import streamablehttp_client_with_sigv4


def get_mcp_url():
    boto_session = Session()
    region = boto_session.region_name
    ssm_client = boto3.client("ssm", region_name=region)
    agent_arn = ssm_client.get_parameter(
        Name="/blog_mcp_math/runtime_iam/agent_arn"
    )["Parameter"]["Value"]
    encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
    return f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT", region


def create_transport(mcp_url: str, region: str):
    session = boto3.Session()
    credentials = session.get_credentials()
    return streamablehttp_client_with_sigv4(
        url=mcp_url,
        credentials=credentials,
        service="bedrock-agentcore",
        region=region,
    )


@pytest.fixture(scope="module")
def mcp_url_and_region():
    return get_mcp_url()


async def test_list_tools(mcp_url_and_region):
    mcp_url, region = mcp_url_and_region
    async with create_transport(mcp_url, region) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
            tool_names = [t.name for t in result.tools]
            assert "add_numbers_sync" in tool_names
            assert "add_numbers_async" in tool_names
            assert "multiply_numbers_sync" in tool_names
            assert "multiply_numbers_async" in tool_names


async def test_add_numbers_sync(mcp_url_and_region):
    mcp_url, region = mcp_url_and_region
    async with create_transport(mcp_url, region) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("add_numbers_sync", {"a": 3, "b": 5})
            assert result.content[0].text == "8"


async def test_add_numbers_async(mcp_url_and_region):
    mcp_url, region = mcp_url_and_region
    async with create_transport(mcp_url, region) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("add_numbers_async", {"a": 3, "b": 5})
            assert result.content[0].text == "8"


async def test_multiply_numbers_sync(mcp_url_and_region):
    mcp_url, region = mcp_url_and_region
    async with create_transport(mcp_url, region) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("multiply_numbers_sync", {"a": 4, "b": 7})
            assert result.content[0].text == "28"


async def test_multiply_numbers_async(mcp_url_and_region):
    mcp_url, region = mcp_url_and_region
    async with create_transport(mcp_url, region) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("multiply_numbers_async", {"a": 4, "b": 7})
            assert result.content[0].text == "28"
