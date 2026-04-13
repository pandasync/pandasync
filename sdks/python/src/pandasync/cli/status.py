"""pandasync status -- show device and network status."""

from __future__ import annotations

import click
import httpx
from rich.console import Console
from rich.table import Table


@click.command()
@click.option("--host", default="127.0.0.1", help="Device API host.")
@click.option("--port", "-p", default=9820, type=int, help="Device API port.")
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Continuously watch status updates.",
)
def status(host: str, port: int, watch: bool) -> None:
    """Show the status of a PandaSync device."""
    console = Console()

    if watch:
        console.print("[yellow]Watch mode is not yet implemented.[/yellow]")
        return

    url = f"http://{host}:{port}/api/v1/status"
    try:
        resp = httpx.get(url, timeout=3.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError:
        console.print(f"[red]Could not reach device at {host}:{port}[/red]")
        console.print(
            "Make sure a PandaSync device is running (start one with: pandasync serve)"
        )
        return

    table = Table(title="PandaSync Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", data.get("version", "unknown"))
    table.add_row("Clock Status", data.get("clock_status", "unknown"))
    table.add_row("Clock Role", data.get("clock_role", "unknown"))
    table.add_row("Clock Offset (us)", str(data.get("clock_offset_us", 0.0)))
    table.add_row("Active Connections", str(data.get("active_connections", 0)))
    table.add_row("Uptime (s)", f"{data.get('uptime_seconds', 0.0):.1f}")

    console.print(table)
