# CLAUDE.md — AWS AgentCore POC

## Project Overview

This is a POC project for AWS AgentCore, built with Python and deployed to AWS using Terraform. As a POC, keep code simple and pragmatic — avoid over-engineering.

---

## Critical Rules

- **NEVER** push to GitHub unless ALL unit tests and integration tests pass.
- **NEVER** commit AWS credentials, secrets, or API keys. Use `.env` files and ensure `.env` is in `.gitignore`.
- **NEVER** run `terraform apply` without first running `terraform plan` and reviewing the output.
- **NEVER** hardcode AWS account IDs, regions, or resource ARNs. Use environment variables or Terraform outputs.
- **ALWAYS** use `uv` for Python package management.
- **ALWAYS** open a PR for review — never push directly to `main` or `dev`.

---

## Project Structure

```
project/
├── src/
│   └── <package_name>/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── infra/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   ├── backend.tf
│   └── modules/
├── .github/
│   └── workflows/
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Python Development

### Package Management

- Use `uv` for all dependency management. Declare dependencies in `pyproject.toml`.

### Code Style

- Follow PEP 8. Use `ruff` for linting and formatting.
- Use type hints on function signatures.
- Use snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants.
- Line length: 88 characters. Use f-strings. Use `logging` instead of `print`.

### Documentation

- Add docstrings only for non-trivial functions and classes where the intent isn't obvious from the code.

### Error Handling

- This is a POC — keep exception handling minimal. Avoid bare `except:`, catch specific exceptions where it matters.
- Use `boto3` session-based credentials or IAM roles — never hardcode keys.

---

## Testing

- Use `pytest`. Follow Arrange-Act-Assert. Tests must be independent.
- Mock AWS services with `moto` in unit tests.
- Mark integration tests with `@pytest.mark.integration`.
- Run unit tests: `uv run pytest tests/unit/ -v`
- Run integration tests: `uv run pytest tests/integration/ -v -m integration`

---

## Terraform

- All infra in `infra/`. Use modules for reusable components.
- Store state in S3 with DynamoDB locking.
- Tag all resources with Project, Environment, ManagedBy.
- Always run `terraform fmt` and `terraform validate` before committing.
- Workflow: `terraform init` → `terraform plan -out=tfplan` → `terraform apply tfplan`

---

## GitHub Workflow

### Branch Strategy

- `main` — production-ready, deploy on merge.
- Feature branches: `feature/<description>` from `main`.

### Pre-Push Checklist

1. `uv run ruff format src/ tests/ && uv run ruff check src/ tests/ --fix`
2. `uv run pytest tests/unit/ -v`
3. `terraform fmt -check && terraform validate` (if infra changed)

### Commit Messages

Use conventional commits: `feat`, `fix`, `test`, `infra`, `docs`, `refactor`, `ci`, `chore`
Example: `feat(agent): add AgentCore invoke handler`

---

## Troubleshooting with CloudWatch

- Use the CloudWatch MCP server to query logs directly from Claude Code.
- Log group convention: `/aws/<service>/<project>/<environment>`.
- Use structured JSON logging with request IDs for traceability.
