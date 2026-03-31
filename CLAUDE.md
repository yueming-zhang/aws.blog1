# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AWS Bedrock AgentCore MCP server demo and blog series project. Implements a FastMCP-based math tools server deployed on Bedrock AgentCore Runtime, with test harness for measuring session management, cold/warm start performance, and observability.

## Key Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r src/mcp_server/requirements.txt

# Run MCP server locally (port 9000)
python src/mcp_server/mcp_server.py

# Run tests against deployed AgentCore endpoint
python src/mcp_server/mcp_test.py async --calls 15 --session shared
python src/mcp_server/mcp_test.py sync --calls 10 --session unique

# Build Docker image for deployment
docker build -t blog_mcp_math src/mcp_server/

# Deploy to Bedrock AgentCore (from src/mcp_server/ directory)
cd src/mcp_server && bedrock-agentcore deploy
```

## Architecture

### `src/mcp_server/` — MCP Server

- **`mcp_server.py`** — FastMCP server exposing sync/async math tools (`add_numbers_sync`, `multiply_numbers_async`, `greet_user`, etc.). Each server instance generates a unique ID to track session-to-VM mapping. Integrates OpenTelemetry tracing.
- **`mcp_test.py`** — Concurrent test client. Spawns parallel MCP tool invocations via `asyncio.gather`, measures wall time and per-call duration, reports server instance distribution. Supports `--calls`, `--session` (unique/shared) CLI args.
- **`streamable_http_sigv4.py`** — Custom HTTPX auth handler for AWS SigV4 request signing against Bedrock AgentCore Runtime. Extends MCP's `StreamableHTTPTransport` with IAM auth and session ID header management.
- **`.bedrock_agentcore.yaml`** — AgentCore deployment config. Agent: `blog_mcp_math`, region: `us-west-2`, platform: `linux/arm64`, protocol: MCP, observability enabled.

### Other

- **`blog/`** — Multi-part blog series on Bedrock AgentCore performance (Firecracker VMs, session lifecycle, cold starts, OpenTelemetry).

## Key Patterns

- Sessions map 1:1 to Firecracker VM instances — unique session IDs yield separate VMs, shared sessions reuse the same VM
- The server returns its instance UUID in tool responses to verify session isolation
- OpenTelemetry instrumentation is applied at the Docker entrypoint level (`opentelemetry-instrument python -m mcp_server`)
- AWS auth uses SigV4 signing via boto3 credentials, not API keys
