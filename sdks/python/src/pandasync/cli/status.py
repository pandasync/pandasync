"""pandasync status -- show device and network status."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from pandasync._version import __version__


@click.command()
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Continuously watch status updates.",
)
def status(watch: bool) -> None:
    """Show the status of the local PandaSync device."""
    console = Console()

    if watch:
        console.print("[yellow]Watch mode is not yet implemented.[/yellow]")
        return

    table = Table(title="PandaSync Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Clock Status", "free_run")
    table.add_row("Clock Role", "listener")
    table.add_row("Active Connections", "0")
    table.add_row("Discovery Tiers", "mdns")

    console.print(table)
