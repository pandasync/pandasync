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

    status_url = f"http://{host}:{port}/api/v1/status"
    streams_url = f"http://{host}:{port}/api/v1/streams"

    try:
        status_resp = httpx.get(status_url, timeout=3.0)
        status_resp.raise_for_status()
        status_data = status_resp.json()
    except httpx.HTTPError:
        console.print(f"[red]Could not reach device at {host}:{port}[/red]")
        console.print(
            "Make sure a PandaSync device is running (start one with: pandasync serve)"
        )
        return

    # Main status table
    table = Table(title="PandaSync Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", status_data.get("version", "unknown"))
    table.add_row("Clock Status", status_data.get("clock_status", "unknown"))
    table.add_row("Clock Role", status_data.get("clock_role", "unknown"))
    table.add_row("Clock Offset (us)", str(status_data.get("clock_offset_us", 0.0)))
    table.add_row(
        "Active Connections",
        str(status_data.get("active_connections", 0)),
    )
    table.add_row("Uptime (s)", f"{status_data.get('uptime_seconds', 0.0):.1f}")
    console.print(table)

    # Active streams table
    try:
        streams_resp = httpx.get(streams_url, timeout=3.0)
        streams_resp.raise_for_status()
        streams = streams_resp.json()
    except httpx.HTTPError:
        return

    if not streams:
        return

    streams_table = Table(title="Active Streams")
    streams_table.add_column("Stream ID", style="cyan")
    streams_table.add_column("Role", style="magenta")
    streams_table.add_column("Source", style="yellow")
    streams_table.add_column("Peer")
    streams_table.add_column("Packets", justify="right", style="green")
    streams_table.add_column("Bytes", justify="right")
    streams_table.add_column("Rate (pps)", justify="right")

    for s in streams:
        sid = s.get("stream_id", "")[:8]
        role = s.get("role", "?")
        src = s.get("source_desc", "")
        if role == "sender":
            peer = f"{s.get('dest_host', '?')}:{s.get('dest_port', '?')}"
            packets = s.get("packets_sent", 0)
            byts = s.get("bytes_sent", 0)
        else:
            peer_host = s.get("peer_host") or "?"
            peer_port = s.get("peer_port") or "?"
            peer = f"{peer_host}:{peer_port}" if peer_host else ":"
            packets = s.get("packets_received", 0)
            byts = s.get("bytes_received", 0)
        rate = s.get("packets_per_second", 0.0)
        streams_table.add_row(
            sid, role, src, peer, str(packets), str(byts), f"{rate:.1f}"
        )

    console.print(streams_table)
