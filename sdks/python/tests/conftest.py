"""Shared test fixtures."""

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from pandasync.cli.main import cli
from pandasync.control.api import create_app
from pandasync.device import Device


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def device() -> Device:
    """A test Device instance (not started, no mDNS)."""
    return Device(name="TestDevice", channels_in=2, channels_out=2)


@pytest.fixture
def api_client(device: Device) -> TestClient:
    """FastAPI test client backed by a real Device."""
    app = create_app(device=device)
    return TestClient(app)


@pytest.fixture
def invoke(cli_runner: CliRunner):
    """Shorthand for invoking CLI commands."""

    def _invoke(*args: str):
        return cli_runner.invoke(cli, list(args))

    return _invoke
