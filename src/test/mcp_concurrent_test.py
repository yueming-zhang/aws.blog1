import asyncio
import time
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


async def call_tool_once(mcp_url: str, region: str, tool: str, call_id: int) -> float:
    start = time.perf_counter()
    async with create_transport(mcp_url, region) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool, {"a": call_id, "b": call_id})
    duration = time.perf_counter() - start
    print(f"  [{tool}] call {call_id:>2}: {duration:.2f}s  result={result.content[0].text}")
    return duration


async def test_add_numbers_sync_concurrent(mcp_url_and_region):
    mcp_url, region = mcp_url_and_region
    print(f"\nadd_numbers_sync — 10 concurrent calls")
    start = time.perf_counter()
    durations = await asyncio.gather(*[
        call_tool_once(mcp_url, region, "add_numbers_sync", i) for i in range(10)
    ])
    total = time.perf_counter() - start
    print(f"  total wall time: {total:.2f}s  avg per call: {sum(durations)/len(durations):.2f}s")
    assert all(d > 0 for d in durations)


async def test_add_numbers_async_concurrent(mcp_url_and_region):
    mcp_url, region = mcp_url_and_region
    print(f"\nadd_numbers_async — 10 concurrent calls")
    start = time.perf_counter()
    durations = await asyncio.gather(*[
        call_tool_once(mcp_url, region, "add_numbers_async", i) for i in range(10)
    ])
    total = time.perf_counter() - start
    print(f"  total wall time: {total:.2f}s  avg per call: {sum(durations)/len(durations):.2f}s")
    assert all(d > 0 for d in durations)
