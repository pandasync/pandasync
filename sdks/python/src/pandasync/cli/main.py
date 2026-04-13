"""PandaSync CLI entry point."""

import click

from pandasync._version import __version__


@click.group()
@click.version_option(version=__version__, prog_name="pandasync")
def cli() -> None:
    """PandaSync -- networked audio transport.

    Plug-in simplicity. Broadcast grade. Completely open.
    """


# Import and register subcommands
from pandasync.cli.connect import connect as connect_cmd  # noqa: E402
from pandasync.cli.discover import discover as discover_cmd  # noqa: E402
from pandasync.cli.serve import serve as serve_cmd  # noqa: E402
from pandasync.cli.status import status as status_cmd  # noqa: E402

cli.add_command(discover_cmd)
cli.add_command(connect_cmd)
cli.add_command(serve_cmd)
cli.add_command(status_cmd)
