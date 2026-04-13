"""Shared test fixtures."""

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from pandasync.cli.main import cli
from pandasync.control.api import create_app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def api_client() -> TestClient:
    """FastAPI test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def invoke(cli_runner: CliRunner):
    """Shorthand for invoking CLI commands."""
    def _invoke(*args: str):
        return cli_runner.invoke(cli, list(args))
    return _invoke
