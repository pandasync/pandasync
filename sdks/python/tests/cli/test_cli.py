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
        assert "verify" in result.output
        assert "sniff" in result.output

    def test_verify_help(self, invoke):
        result = invoke("verify", "--help")
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--duration" in result.output

    def test_sniff_help(self, invoke):
        result = invoke("sniff", "--help")
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--packets" in result.output
        assert "--expected-freq" in result.output

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
        status_response = {
            "version": __version__,
            "clock_status": "locked",
            "clock_role": "slave",
            "clock_offset_us": 0.5,
            "active_connections": 3,
            "uptime_seconds": 120.0,
        }

        def mock_get(url, **kwargs):
            mock_resp = type(
                "Response",
                (),
                {
                    "status_code": 200,
                    "raise_for_status": lambda self=None: None,
                    "json": lambda self=None: (
                        status_response if "status" in url else []
                    ),
                },
            )()
            return mock_resp

        with patch("pandasync.cli.status.httpx.get", side_effect=mock_get):
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
