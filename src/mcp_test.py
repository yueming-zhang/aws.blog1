import logging
logging.getLogger("mcp.client.streamable_http").setLevel(logging.ERROR)

import asyncio
import time
import uuid
import argparse
import boto3
from boto3.session import Session
from mcp import ClientSession
from streamable_http_sigv4 import streamablehttp_client_with_sigv4


def get_mcp_url():
    boto_session = Session()
    region = boto_session.region_name
    ssm_client = boto3.client("ssm", region_name=region)
    agent_arn = ssm_client.get_parameter(Name="/blog_mcp_math/runtime_iam/agent_arn")["Parameter"]["Value"]
    encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
    return f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT", region


def create_transport(mcp_url: str, region: str, session_id: str | None = None):
    session = boto3.Session()
    credentials = session.get_credentials()
    headers = {"Mcp-Session-Id": session_id} if session_id else None
    return streamablehttp_client_with_sigv4(
        url=mcp_url,
        credentials=credentials,
        service="bedrock-agentcore",
        region=region,
        headers=headers,
    )


def parse_response(text: str) -> tuple[str, str]:
    parts = dict(p.split("=", 1) for p in text.split(" "))
    return parts["result"], parts["server"]


async def call_tool_once(mcp_url: str, region: str, tool: str, call_id: int, session_id: str | None = None) -> tuple[float, str]:
    start = time.perf_counter()
    async with create_transport(mcp_url, region, session_id=session_id) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool, {"a": call_id, "b": call_id})
    duration = time.perf_counter() - start
    value, server_id = parse_response(result.content[0].text)
    print(f"  [{tool}] call {call_id:>2}: {duration:.2f}s  value={value}  server={server_id}")
    return duration, server_id


async def run(tool: str, num_calls: int, shared_session: bool):
    mcp_url, region = get_mcp_url()
    session_id = str(uuid.uuid4()) if shared_session else None
    session_label = f"shared Mcp-Session-Id={session_id}" if shared_session else "unique sessions"

    print(f"\n{tool} — {num_calls} concurrent calls, {session_label}")
    start = time.perf_counter()
    results = await asyncio.gather(*[
        call_tool_once(mcp_url, region, tool, i, session_id=session_id) for i in range(num_calls)
    ])
    total = time.perf_counter() - start
    durations, server_ids = zip(*results)
    print(f"  total wall time: {total:.2f}s  avg per call: {sum(durations)/len(durations):.2f}s")
    print(f"  unique server instances: {len(set(server_ids))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run concurrent MCP tool calls")
    parser.add_argument("mode", choices=["sync", "async"], help="Tool variant to call")
    parser.add_argument("--calls", type=int, default=10, help="Number of concurrent calls (default: 10)")
    parser.add_argument("--session", choices=["unique", "shared"], default="unique", help="Session mode (default: unique)")
    args = parser.parse_args()

    tool = "add_numbers_sync" if args.mode == "sync" else "add_numbers_async"
    asyncio.run(run(tool, args.calls, shared_session=(args.session == "shared")))


#   python mcp_concurrent_test.py async --calls 20 --session shared
#   python mcp_concurrent_test.py sync --calls 5 --session shared
