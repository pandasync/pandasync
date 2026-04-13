"""pandasync connect -- route audio between devices."""

from __future__ import annotations

import click
from rich.console import Console

from pandasync.models import TransportType


@click.command()
@click.argument("source")
@click.argument("destination")
@click.option(
    "--transport",
    "-T",
    type=click.Choice(["auto", "rtp", "quic", "webrtc"]),
    default="auto",
    help="Transport type to use.",
)
def connect(source: str, destination: str, transport: str) -> None:
    """Connect an audio source to a receiver.

    SOURCE and DESTINATION are in the format "DeviceName:channels"
    (e.g., "MicArray:ch1-8").
    """
    console = Console()
    transport_type = TransportType(transport)

    console.print(
        f"Connecting [cyan]{source}[/cyan] -> [cyan]{destination}[/cyan] "
        f"via [green]{transport_type.value}[/green]..."
    )

    # TODO: Resolve source/destination to actual devices and create connection
    console.print("[yellow]Connection routing is not yet fully implemented.[/yellow]")
    console.print(
        "The control plane will resolve device names and establish the route."
    )
