import logging
logging.getLogger("mcp.client.streamable_http").setLevel(logging.ERROR)

import asyncio
import time
from datetime import datetime
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


async def call_tool_once(mcp_url: str, region: str, tool: str, call_id: int, session_id: str | None = None) -> tuple[float, float, float, str]:
    start_time = datetime.now()
    start = time.perf_counter()
    async with create_transport(mcp_url, region, session_id=session_id) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool, {"a": call_id, "b": call_id})
    end = time.perf_counter()
    end_time = datetime.now()
    duration = end - start
    _, server_id = parse_response(result.content[0].text)
    print(f"  {tool} #{call_id:<3} start={start_time:%H:%M:%S}, end={end_time:%H:%M:%S}, duration={duration:>6.2f}s, server={server_id}", flush=True)
    return start, end, duration, server_id


async def delayed_call(mcp_url, region, tool, call_id, interval, session_id):
    """Wait (call_id * interval) seconds before making the call."""
    if interval > 0 and call_id > 0:
        await asyncio.sleep(call_id * interval)
    return await call_tool_once(mcp_url, region, tool, call_id, session_id=session_id)


async def run(tool: str, num_calls: int, shared_session: bool, interval: float = 0):
    mcp_url, region = get_mcp_url()
    session_id = str(uuid.uuid4()) if shared_session else None
    session_label = f"shared Mcp-Session-Id={session_id}" if shared_session else "unique sessions"
    interval_label = f", interval={interval}s" if interval > 0 else ""

    print(f"\n{tool} — {num_calls} calls, {session_label}{interval_label}")
    results = await asyncio.gather(*[
        delayed_call(mcp_url, region, tool, i, interval, session_id=session_id) for i in range(num_calls)
    ])
    starts, ends, durations, server_ids = zip(*results)
    wall_time = max(ends) - min(starts)
    print(f"  total wall time: {wall_time:.2f}s  avg per call: {sum(durations)/len(durations):.2f}s")
    print(f"  unique server instances: {len(set(server_ids))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run concurrent MCP tool calls")
    parser.add_argument("mode", choices=["sync", "async"], help="Tool variant to call")
    parser.add_argument("--calls", type=int, default=10, help="Number of calls (default: 10)")
    parser.add_argument("--session", choices=["unique", "shared"], default="unique", help="Session mode (default: unique)")
    parser.add_argument("--interval", type=float, default=0, help="Delay in seconds between each call (default: 0, all concurrent)")
    args = parser.parse_args()

    tool = "add_numbers_sync" if args.mode == "sync" else "add_numbers_async"
    asyncio.run(run(tool, args.calls, shared_session=(args.session == "shared"), interval=args.interval))

    # python mcp_test.py async --calls 20 --session shared
    # python mcp_test.py async --calls 10 --interval 2 --session unique
