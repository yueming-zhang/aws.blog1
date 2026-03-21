# CLAUDE.md — Python AWS Project with Terraform

## Project Overview

This is a Python project deployed to AWS using Terraform for infrastructure management. All code changes must pass unit and integration tests before being pushed to GitHub.

---

## Critical Rules

- **NEVER** push to GitHub unless ALL unit tests and integration tests pass.
- **NEVER** commit AWS credentials, secrets, or API keys. Use `.env` files and ensure `.env` is in `.gitignore`.
- **NEVER** run `terraform apply` without first running `terraform plan` and reviewing the output.
- **NEVER** hardcode AWS account IDs, regions, or resource ARNs in application code. Use environment variables or Terraform outputs.
- **ALWAYS** run the full test suite (`pytest tests/`) before committing.
- **ALWAYS** use `uv` for Python package management. Create a `.venv` if not present.

---

## Project Structure

```
project/
├── src/                        # Application source code
│   └── <package_name>/
│       ├── __init__.py
│       ├── main.py
│       └── ...
├── tests/
│   ├── unit/                   # Fast, isolated unit tests
│   │   ├── conftest.py
│   │   └── test_*.py
│   ├── integration/            # Tests against real AWS services
│   │   ├── conftest.py
│   │   └── test_*.py
│   └── conftest.py             # Shared fixtures
├── infra/                      # Terraform infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   ├── backend.tf
│   ├── terraform.tfvars        # Do NOT commit if contains secrets
│   └── modules/
│       └── <module_name>/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Run tests on PR
│       └── deploy.yml          # Deploy on merge to main
├── pyproject.toml
├── CLAUDE.md
├── .gitignore
├── .env.example                # Template for environment variables
└── README.md
```

---

## Python Development

### Package Management

- Use `uv` for all dependency management and virtual environment creation.
- All dependencies declared in `pyproject.toml`.
- Pin dependency versions for reproducibility.

### Code Style

- Follow PEP 8. Use `ruff` for linting and formatting.
- Use `mypy` for static type checking with strict mode.
- Use type hints on all function signatures.
- Use snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants.
- Line length limit: 88 characters (ruff default).
- Use f-strings for string formatting.
- Use `logging` module instead of `print` for all output.

### Documentation

- Docstrings required on all public functions, classes, and methods.
- Use Google-style docstrings with Args, Returns, and Raises sections.
- Keep docstrings in sync with code changes.

### Error Handling

- Never use bare `except:` clauses.
- Catch specific exceptions.
- Use context managers (`with` statements) for resource cleanup.
- Log errors with `logger.error()` including relevant context.

### Security

- Store all secrets in `.env` (never commit this file).
- Use `boto3` session-based credentials or IAM roles — never hardcode keys.
- Validate and sanitize all external inputs.

---

## Testing

### General Rules

- Use `pytest` as the testing framework.
- Follow the Arrange-Act-Assert pattern.
- Tests must be independent and not rely on execution order.
- Mock external dependencies in unit tests (AWS services, APIs, databases).
- Use `pytest-cov` for coverage reporting. Target: 80%+ line coverage.
- Save test files before running them. Never run inline test code.
- Never delete test files or test output files.
- Ensure test output directories are in `.gitignore`.

### Unit Tests (`tests/unit/`)

- Fast, isolated, no network or AWS calls.
- Use `moto` to mock AWS services (S3, DynamoDB, Lambda, SQS, etc.).
- Use `pytest` fixtures and `conftest.py` for shared setup.
- Use `@pytest.mark.parametrize` for data-driven tests.
- One test file per source module: `test_<module_name>.py`.

Example:
```python
import pytest
from moto import mock_aws

@mock_aws
def test_upload_to_s3(s3_client, sample_data):
    """Test that data is correctly uploaded to S3."""
    # Arrange
    bucket = "test-bucket"
    s3_client.create_bucket(Bucket=bucket)

    # Act
    result = upload_data(s3_client, bucket, "key.json", sample_data)

    # Assert
    assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
```

### Integration Tests (`tests/integration/`)

- Test against real AWS services in a dev/test account.
- Mark with `@pytest.mark.integration` so they can be run separately.
- Use dedicated test resources (prefixed with `test-` or in a test environment).
- Clean up all created resources in teardown/fixtures.
- Require AWS credentials to be configured (skip gracefully if not available).
- These are slower — run separately from unit tests in CI.

Example:
```python
import pytest

@pytest.mark.integration
def test_lambda_invocation(deployed_lambda_name):
    """Test that the deployed Lambda function responds correctly."""
    import boto3
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName=deployed_lambda_name,
        Payload=json.dumps({"action": "health_check"}),
    )
    payload = json.loads(response["Payload"].read())
    assert payload["statusCode"] == 200
```

### Running Tests

```bash
# Run unit tests only (fast, no AWS needed)
uv run pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Run integration tests only (requires AWS credentials)
uv run pytest tests/integration/ -v -m integration

# Run all tests
uv run pytest tests/ -v --cov=src

# Run with parallel execution
uv run pytest tests/unit/ -v -n auto
```

### pytest Configuration (in `pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "integration: marks tests that require real AWS services",
]
addopts = "--strict-markers"
```

---

## Terraform / Infrastructure

### Structure

- All infrastructure code lives in `infra/`.
- Use modules for reusable components (`infra/modules/`).
- Use `terraform.tfvars` for environment-specific values (do not commit secrets).
- Store Terraform state in S3 with DynamoDB locking.

### Provider Configuration (`infra/provider.tf`)

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

### Backend Configuration (`infra/backend.tf`)

```hcl
terraform {
  backend "s3" {
    bucket         = "<project>-terraform-state"
    key            = "state/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "<project>-terraform-locks"
    encrypt        = true
  }
}
```

### Conventions

- Use descriptive resource names with project and environment prefixes.
- Tag all resources with Project, Environment, and ManagedBy.
- Use `variable` blocks with descriptions and validation where appropriate.
- Use `output` blocks to expose values needed by the application.
- Use `locals` for computed values to keep code DRY.
- Use `terraform fmt` before committing.
- Use `terraform validate` as part of CI.

### Terraform Workflow

```bash
cd infra/

# Initialize (first time or after backend changes)
terraform init

# Format check
terraform fmt -check

# Validate
terraform validate

# Plan (always review before apply)
terraform plan -out=tfplan

# Apply (only after reviewing plan)
terraform apply tfplan

# Destroy (use with caution)
terraform destroy
```

---

## GitHub Workflow

### Branch Strategy

- `main` — production-ready code, deploy on merge.
- `dev` — integration branch for feature work.
- Feature branches: `feature/<description>` from `dev`.
- Bugfix branches: `fix/<description>`.

### Pre-Push Checklist

Before pushing any branch, run ALL of the following:

```bash
# 1. Format and lint
uv run ruff format src/ tests/
uv run ruff check src/ tests/ --fix

# 2. Type check
uv run mypy src/

# 3. Unit tests with coverage
uv run pytest tests/unit/ -v --cov=src --cov-report=term-missing

# 4. Integration tests (if AWS credentials available)
uv run pytest tests/integration/ -v -m integration

# 5. Terraform checks (if infra changes)
cd infra/ && terraform fmt -check && terraform validate && cd ..
```

**Only push if ALL steps pass.** If any step fails, fix the issue first.

### Commit Messages

Use conventional commits:

```
<type>(<scope>): <short description>

<optional body>
```

Types: `feat`, `fix`, `test`, `infra`, `docs`, `refactor`, `ci`, `chore`

Examples:
- `feat(api): add health check endpoint`
- `infra(lambda): add CloudWatch alarm for error rate`
- `test(unit): add tests for S3 upload handler`
- `fix(auth): handle expired token refresh`

### CI/CD Pipeline (`.github/workflows/ci.yml`)

The CI pipeline should:

1. Install dependencies with `uv`.
2. Run `ruff` format and lint checks.
3. Run `mypy` type checking.
4. Run unit tests with coverage.
5. Run `terraform fmt -check` and `terraform validate` for infra changes.
6. Run integration tests (on `main` and `dev` branches only, with AWS credentials from GitHub secrets).

### Deploy Pipeline (`.github/workflows/deploy.yml`)

Triggered on merge to `main`:

1. Run full test suite (unit + integration).
2. Run `terraform plan` and output for review.
3. Run `terraform apply` (auto-approve in CI, or require manual approval).
4. Deploy application code (package Lambda, update ECS, etc.).
5. Run smoke tests against deployed environment.

---

## Troubleshooting with CloudWatch

- Use the CloudWatch MCP server to query logs directly from Claude Code.
- Log group naming convention: `/aws/<service>/<project>/<environment>`.
- Include request IDs and correlation IDs in all log messages for traceability.
- Use structured logging (JSON format) for easier querying.

```python
import logging
import json

logger = logging.getLogger(__name__)

def log_event(event_type: str, **kwargs):
    logger.info(json.dumps({"event": event_type, **kwargs}))
```

---

## Before Handing Off Code

- All unit and integration tests pass.
- Type checking passes (`mypy --strict`).
- Linting and formatting pass (`ruff`).
- All functions have docstrings and type hints.
- No commented-out code or debug statements.
- No hardcoded credentials or secrets.
- Terraform is formatted and validated.
- Commit messages follow conventional commits.
- README is up to date.