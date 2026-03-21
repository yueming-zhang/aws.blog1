"""Create or update an AgentCore runtime and store the ARN in SSM.

Called by Terraform null_resource. Usage:
    uv run python infra/scripts/agentcore_runtime.py \\
        --agent-name <name> \\
        --ecr-uri <ecr_image_uri> \\
        --role-arn <iam_role_arn> \\
        --region <aws_region> \\
        --ssm-param <ssm_parameter_name>
"""

from __future__ import annotations

import argparse
import logging
import time

import boto3

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"READY", "CREATE_FAILED", "UPDATE_FAILED", "DELETE_FAILED"}


def find_runtime(client, agent_name: str) -> dict | None:
    paginator = client.get_paginator("list_agent_runtimes")
    for page in paginator.paginate():
        for runtime in page.get("agentRuntimes", []):
            if runtime.get("agentRuntimeName") == agent_name:
                return runtime
    return None


def wait_for_ready(client, agent_runtime_id: str) -> str:
    while True:
        response = client.get_agent_runtime(agentRuntimeId=agent_runtime_id)
        status = response["status"]
        logger.info("Status: %s", status)
        if status in TERMINAL_STATUSES:
            return status
        time.sleep(10)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--ecr-uri", required=True)
    parser.add_argument("--role-arn", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--ssm-param", required=True)
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    ssm = boto3.client("ssm", region_name=args.region)

    artifact = {"containerConfiguration": {"containerUri": args.ecr_uri}}

    existing = find_runtime(client, args.agent_name)

    if existing:
        runtime_id = existing["agentRuntimeId"]
        logger.info("Updating existing runtime %s", runtime_id)
        client.update_agent_runtime(
            agentRuntimeId=runtime_id,
            agentRuntimeArtifact=artifact,
        )
    else:
        logger.info("Creating new runtime '%s'", args.agent_name)
        response = client.create_agent_runtime(
            agentRuntimeName=args.agent_name,
            agentRuntimeArtifact=artifact,
            networkConfiguration={"networkMode": "PUBLIC"},
            protocolConfiguration={"serverProtocol": "MCP"},
            roleArn=args.role_arn,
        )
        runtime_id = response["agentRuntimeId"]

    status = wait_for_ready(client, runtime_id)
    if status != "READY":
        logger.error("Runtime ended with status: %s", status)
        return 1

    response = client.get_agent_runtime(agentRuntimeId=runtime_id)
    agent_arn = response["agentRuntimeArn"]
    logger.info("Runtime ready: %s", agent_arn)

    ssm.put_parameter(
        Name=args.ssm_param, Value=agent_arn, Type="String", Overwrite=True
    )
    logger.info("ARN stored in SSM parameter: %s", args.ssm_param)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
