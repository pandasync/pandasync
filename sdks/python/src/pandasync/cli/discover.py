"""pandasync discover -- find devices on the network."""

from __future__ import annotations

import time

import click
from rich.console import Console
from rich.table import Table

from pandasync.discovery.manager import DiscoveryManager


@click.command()
@click.option(
    "--timeout",
    "-t",
    default=3.0,
    type=float,
    help="Discovery timeout in seconds.",
)
@click.option(
    "--tier",
    multiple=True,
    default=["mdns"],
    help="Discovery tiers to use (mdns, dns_sd, cloud).",
)
def discover(timeout: float, tier: tuple[str, ...]) -> None:
    """Discover PandaSync devices on the network."""
    console = Console()

    with console.status("Scanning for devices..."):
        manager = DiscoveryManager(tiers=list(tier))
        manager.start()
        time.sleep(timeout)
        devices = manager.discover()
        manager.stop()

    if not devices:
        console.print("[yellow]No devices found.[/yellow]")
        console.print("Make sure other PandaSync devices are running on your network.")
        return

    table = Table(title="Discovered Devices")
    table.add_column("Name", style="cyan")
    table.add_column("Host", style="green")
    table.add_column("Port")
    table.add_column("Channels In")
    table.add_column("Channels Out")
    table.add_column("Profile")
    table.add_column("Version")

    for device in devices:
        table.add_row(
            device.name,
            device.host,
            str(device.port),
            str(device.channels_in),
            str(device.channels_out),
            device.profile,
            device.version,
        )

    console.print(table)
    console.print(f"\n[green]{len(devices)} device(s) found.[/green]")
