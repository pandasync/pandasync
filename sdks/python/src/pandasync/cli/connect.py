"""pandasync connect -- route audio between devices."""

from __future__ import annotations

import time

import click
import httpx
from rich.console import Console

from pandasync.discovery.manager import DiscoveryManager


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
@click.option(
    "--timeout",
    default=3.0,
    type=float,
    help="Discovery timeout in seconds.",
)
def connect(
    source: str,
    destination: str,
    transport: str,
    timeout: float,
) -> None:
    """Connect an audio source to a receiver.

    SOURCE and DESTINATION are in the format "DeviceName:channel"
    (e.g., "SkwadMixer:out1").
    """
    console = Console()

    src_device_name = source.split(":", 1)[0]

    # Discover devices to find the source's API endpoint
    with console.status(f"Locating {src_device_name}..."):
        manager = DiscoveryManager(tiers=["mdns"])
        manager.start()
        time.sleep(timeout)
        devices = manager.discover()
        manager.stop()

    src_device = next((d for d in devices if d.name == src_device_name), None)
    if src_device is None:
        console.print(
            f"[red]Source device '{src_device_name}' not found on the network.[/red]"
        )
        console.print(
            f"Discovered {len(devices)} device(s): "
            + ", ".join(d.name for d in devices)
        )
        return

    url = f"http://{src_device.host}:{src_device.port}/api/v1/connect"
    console.print(
        f"Connecting [cyan]{source}[/cyan] -> "
        f"[cyan]{destination}[/cyan] via [green]{transport}[/green]..."
    )

    try:
        resp = httpx.post(
            url,
            json={
                "source": source,
                "destination": destination,
                "transport": transport,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        console.print(
            f"[red]Connection failed ({e.response.status_code}):[/red] "
            f"{e.response.text}"
        )
        return
    except httpx.HTTPError as e:
        console.print(f"[red]Connection failed:[/red] {e}")
        return

    console.print(
        f"[green]Connection established.[/green] "
        f"ID: [yellow]{data['connection_id']}[/yellow]"
    )
    console.print(
        f"  {data['source']} -> {data['destination']} via {data['transport']}"
    )
    console.print(
        "\nUse [cyan]pandasync status[/cyan] "
        f"--host {src_device.host} to monitor the stream."
    )
