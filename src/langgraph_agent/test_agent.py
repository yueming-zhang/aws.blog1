import logging

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("botocore").setLevel(logging.ERROR)

import asyncio
import time
from datetime import datetime
import uuid
import argparse

import httpx
import boto3
from boto3.session import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


SESSION_HEADER = "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"


def get_agent_url():
    boto_session = Session()
    region = boto_session.region_name
    ssm_client = boto3.client("ssm", region_name=region)
    agent_arn = ssm_client.get_parameter(Name="/blog_langgraph_agent/runtime_iam/agent_arn")["Parameter"]["Value"]
    encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
    return f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT", region


class SigV4Auth_HTTPX(httpx.Auth):
    """HTTPX Auth that signs requests with AWS SigV4."""

    def __init__(self, credentials, service: str, region: str):
        self.signer = SigV4Auth(credentials, service, region)

    def auth_flow(self, request: httpx.Request):
        headers = dict(request.headers)
        headers.pop("connection", None)
        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers,
        )
        self.signer.add_auth(aws_request)
        request.headers.update(dict(aws_request.headers))
        yield request


def create_httpx_auth(region: str):
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    return SigV4Auth_HTTPX(credentials, "bedrock-agentcore", region)


async def call_agent_once(
    agent_url: str,
    region: str,
    call_id: int,
    session_id: str | None = None,
) -> tuple[float, float, float, str]:
    start_time = datetime.now()
    start = time.perf_counter()

    auth = create_httpx_auth(region)
    headers = {"Content-Type": "application/json"}
    if session_id:
        headers[SESSION_HEADER] = session_id

    payload = {
        "prompt": f"add {call_id} and {call_id}",
    }

    async with httpx.AsyncClient(auth=auth, timeout=120) as client:
        response = await client.post(agent_url, json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()

    end = time.perf_counter()
    end_time = datetime.now()
    duration = end - start

    server_id = body.get("server", "unknown")
    result_text = body.get("result", "")
    # Truncate long LLM responses for display
    display_result = result_text[:80] + "..." if len(result_text) > 80 else result_text

    print(
        f"  agent #{call_id:<3} start={start_time:%H:%M:%S}, end={end_time:%H:%M:%S}, "
        f"duration={duration:>6.2f}s, server={server_id}  result={display_result}",
        flush=True,
    )
    return start, end, duration, server_id


async def delayed_call(agent_url, region, call_id, interval, session_id):
    """Wait (call_id * interval) seconds before making the call."""
    if interval > 0 and call_id > 0:
        await asyncio.sleep(call_id * interval)
    return await call_agent_once(agent_url, region, call_id, session_id=session_id)


async def run(num_calls: int, shared_session: bool, interval: float = 0):
    agent_url, region = get_agent_url()
    session_id = str(uuid.uuid4()) if shared_session else None
    session_label = f"shared session={session_id}" if shared_session else "unique sessions"
    interval_label = f", interval={interval}s" if interval > 0 else ""

    print(f"\nlanggraph agent — {num_calls} calls, {session_label}{interval_label}")
    results = await asyncio.gather(*[
        delayed_call(agent_url, region, i, interval, session_id=session_id)
        for i in range(num_calls)
    ])
    starts, ends, durations, server_ids = zip(*results)
    wall_time = max(ends) - min(starts)
    print(f"  total wall time: {wall_time:.2f}s  avg per call: {sum(durations)/len(durations):.2f}s")
    print(f"  unique server instances: {len(set(server_ids))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run concurrent LangGraph agent calls")
    parser.add_argument("--calls", type=int, default=5, help="Number of calls (default: 5)")
    parser.add_argument("--session", choices=["unique", "shared"], default="unique", help="Session mode (default: unique)")
    parser.add_argument("--interval", type=float, default=0, help="Delay in seconds between each call (default: 0, all concurrent)")
    args = parser.parse_args()

    asyncio.run(run(args.calls, shared_session=(args.session == "shared"), interval=args.interval))

    # python test_agent.py --calls 5 --session unique
    # python test_agent.py --calls 5 --session shared
    # python test_agent.py --calls 10 --interval 2 --session unique
