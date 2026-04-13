"""Tests for the CLI."""

from pandasync._version import __version__


class TestCLI:
    def test_help(self, invoke):
        result = invoke("--help")
        assert result.exit_code == 0
        assert "PandaSync" in result.output
        assert "discover" in result.output
        assert "connect" in result.output
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

    def test_status_help(self, invoke):
        result = invoke("status", "--help")
        assert result.exit_code == 0
        assert "--watch" in result.output

    def test_status_output(self, invoke):
        result = invoke("status")
        assert result.exit_code == 0
        assert "PandaSync Status" in result.output
        assert __version__ in result.output

    def test_connect_requires_args(self, invoke):
        result = invoke("connect")
        assert result.exit_code != 0
