"""Tests for the CLI."""

from unittest.mock import patch

from pandasync._version import __version__


class TestCLI:
    def test_help(self, invoke):
        result = invoke("--help")
        assert result.exit_code == 0
        assert "PandaSync" in result.output
        assert "discover" in result.output
        assert "connect" in result.output
        assert "serve" in result.output
        assert "status" in result.output

    def test_version(self, invoke):
        result = invoke("--version")
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_discover_help(self, invoke):
        result = invoke("discover", "--help")
        assert result.exit_code == 0
        assert "--timeout" in result.output
        assert "--tier" in result.output

    def test_connect_help(self, invoke):
        result = invoke("connect", "--help")
        assert result.exit_code == 0
        assert "SOURCE" in result.output
        assert "DESTINATION" in result.output
        assert "--transport" in result.output

    def test_serve_help(self, invoke):
        result = invoke("serve", "--help")
        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--port" in result.output
        assert "--channels-in" in result.output
        assert "--channels-out" in result.output
        assert "--profile" in result.output

    def test_status_help(self, invoke):
        result = invoke("status", "--help")
        assert result.exit_code == 0
        assert "--watch" in result.output
        assert "--host" in result.output
        assert "--port" in result.output

    def test_status_queries_api(self, invoke):
        mock_response = {
            "version": __version__,
            "clock_status": "locked",
            "clock_role": "slave",
            "clock_offset_us": 0.5,
            "active_connections": 3,
            "uptime_seconds": 120.0,
        }
        with patch("pandasync.cli.status.httpx.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None
            result = invoke("status")

        assert result.exit_code == 0
        assert "PandaSync Status" in result.output
        assert "locked" in result.output
        assert "slave" in result.output

    def test_status_unreachable(self, invoke):
        import httpx

        with patch(
            "pandasync.cli.status.httpx.get",
            side_effect=httpx.ConnectError("refused"),
        ):
            result = invoke("status")

        assert result.exit_code == 0
        assert "Could not reach device" in result.output

    def test_connect_requires_args(self, invoke):
        result = invoke("connect")
        assert result.exit_code != 0
