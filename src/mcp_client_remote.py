import asyncio
import sys
import logging
import boto3
from boto3.session import Session
from mcp import ClientSession
from streamable_http_sigv4 import streamablehttp_client_with_sigv4

logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_streamable_http_transport_sigv4(mcp_url: str, service_name: str, region: str):
    session = boto3.Session()
    credentials = session.get_credentials()
    return streamablehttp_client_with_sigv4(
        url=mcp_url,
        credentials=credentials,
        service=service_name,
        region=region,
    )


async def main():
    boto_session = Session()
    region = boto_session.region_name
    print(f"Using AWS region: {region}")

    ssm_client = boto3.client("ssm", region_name=region)
    agent_arn = ssm_client.get_parameter(
        Name="/blog_mcp_math/runtime_iam/agent_arn"
    )["Parameter"]["Value"]
    print(f"Retrieved Agent ARN: {agent_arn}")

    encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"

    try:
        async with create_streamable_http_transport_sigv4(
            mcp_url=mcp_url, service_name="bedrock-agentcore", region=region
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tool_result = await session.list_tools()

                print("\nAvailable MCP Tools:")
                print("=" * 50)
                for tool in tool_result.tools:
                    print(f"  {tool.name}: {tool.description}")
                    if hasattr(tool, "inputSchema") and tool.inputSchema:
                        properties = tool.inputSchema.get("properties", {})
                        if properties:
                            print(f"    Parameters: {list(properties.keys())}")

                print(f"\nFound {len(tool_result.tools)} tools available.")

                print("\nTesting add_numbers(3, 5)...")
                result = await session.call_tool("add_numbers", {"a": 3, "b": 5})
                print(f"Result: {result.content[0].text}")

    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
