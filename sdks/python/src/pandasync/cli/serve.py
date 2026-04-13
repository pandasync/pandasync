"""pandasync serve -- run a PandaSync device node with API server."""

from __future__ import annotations

import click
from rich.console import Console


@click.command()
@click.option("--name", "-n", default="PandaSync Device", help="Device name.")
@click.option("--channels-in", default=2, type=int, help="Number of input channels.")
@click.option("--channels-out", default=2, type=int, help="Number of output channels.")
@click.option("--host", default="0.0.0.0", help="API server bind address.")
@click.option("--port", "-p", default=9820, type=int, help="API server port.")
@click.option(
    "--profile",
    type=click.Choice(["simple", "broadcast", "developer"]),
    default="simple",
    help="Operational profile.",
)
def serve(
    name: str,
    channels_in: int,
    channels_out: int,
    host: str,
    port: int,
    profile: str,
) -> None:
    """Run a PandaSync device node with the REST API server."""
    from pandasync.device import Device
    from pandasync.profiles import Profile

    console = Console()
    device = Device(
        name=name,
        channels_in=channels_in,
        channels_out=channels_out,
        profile=Profile(profile),
    )

    console.print(f"Starting [cyan]{name}[/cyan] on {host}:{port}...")
    console.print(f"  Channels: {channels_in} in / {channels_out} out")
    console.print(f"  Profile: {profile}")
    console.print(f"  API docs: http://{host}:{port}/api/docs")
    console.print()

    try:
        device.serve(host=host, port=port)
    except KeyboardInterrupt:
        device.stop()
        console.print("\n[yellow]Device stopped.[/yellow]")
