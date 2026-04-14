"""pandasync verify -- measure RTP transport health against thresholds."""

from __future__ import annotations

import time
from typing import Any

import click
import httpx
from rich.console import Console
from rich.live import Live
from rich.table import Table


def _make_table(stream: dict[str, Any]) -> Table:
    """Render the current stream stats as a Rich table."""
    table = Table(title=f"Stream: {stream.get('source_desc', '?')}", expand=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    role = stream.get("role", "?")
    table.add_row("Role", role)
    if role == "receiver":
        peer = f"{stream.get('peer_host', '?')}:{stream.get('peer_port', '?')}"
        table.add_row("Peer", peer)
        table.add_row("Packets received", str(stream.get("packets_received", 0)))
        table.add_row("Bytes received", str(stream.get("bytes_received", 0)))
        table.add_row("Sequence gaps", str(stream.get("sequence_gaps", 0)))
        table.add_row(
            "Verification errors",
            str(stream.get("verification_errors", 0)),
        )
        table.add_row("Rate (pps)", f"{stream.get('packets_per_second', 0):.1f}")

        jitter = stream.get("jitter", {}) or {}
        if jitter.get("mean_ms") is not None:
            table.add_row(
                "Jitter mean",
                f"{jitter['mean_ms']:.3f} ms",
            )
            table.add_row(
                "Jitter stddev",
                f"{jitter['stddev_ms']:.3f} ms",
            )
            table.add_row(
                "Jitter max",
                f"{jitter['max_ms']:.3f} ms",
            )
    else:
        dest = f"{stream.get('dest_host', '?')}:{stream.get('dest_port', '?')}"
        table.add_row("Dest", dest)
        table.add_row("Packets sent", str(stream.get("packets_sent", 0)))
        table.add_row("Packets dropped", str(stream.get("packets_dropped", 0)))
        table.add_row("Rate (pps)", f"{stream.get('packets_per_second', 0):.1f}")

    return table


def _compute_drift_ppm(first: dict[str, Any], last: dict[str, Any]) -> float | None:
    """Compute clock drift in PPM by comparing latency change over time."""
    try:
        first_latency = first["latency"]["mean_ns"]
        last_latency = last["latency"]["mean_ns"]
        first_uptime = first["uptime_seconds"]
        last_uptime = last["uptime_seconds"]
    except (KeyError, TypeError):
        return None
    if first_latency is None or last_latency is None:
        return None
    dt = float(last_uptime) - float(first_uptime)
    if dt <= 0:
        return None
    drift_ns = float(last_latency) - float(first_latency)
    return (drift_ns / (dt * 1e9)) * 1e6


@click.command()
@click.option("--host", required=True, help="Receiver API host.")
@click.option("--port", "-p", default=9820, type=int, help="Receiver API port.")
@click.option("--stream-id", default=None, help="Specific stream to monitor.")
@click.option(
    "--duration",
    "-d",
    default=30,
    type=int,
    help="Verification duration in seconds.",
)
@click.option(
    "--max-loss",
    default=0.001,
    type=float,
    help="Max acceptable loss rate (0.0-1.0).",
)
@click.option(
    "--max-jitter-stddev-ms",
    default=0.5,
    type=float,
    help="Max acceptable jitter stddev in ms.",
)
@click.option(
    "--max-jitter-ms",
    default=5.0,
    type=float,
    help="Max acceptable jitter peak in ms.",
)
def verify(
    host: str,
    port: int,
    stream_id: str | None,
    duration: int,
    max_loss: float,
    max_jitter_stddev_ms: float,
    max_jitter_ms: float,
) -> None:
    """Verify transport health on a running receiver.

    Polls the receiver's /api/v1/streams endpoint every second and compares
    measured jitter, loss, and drift against configured thresholds.
    """
    console = Console()
    base_url = f"http://{host}:{port}/api/v1/streams"

    first_snapshot: dict[str, Any] | None = None
    last_snapshot: dict[str, Any] | None = None
    start_time = time.monotonic()
    end_time = start_time + duration

    console.print(
        f"[cyan]Verifying[/cyan] {host}:{port} for {duration}s "
        f"(max loss: {max_loss * 100:.2f}%, "
        f"max jitter stddev: {max_jitter_stddev_ms:.2f}ms, "
        f"max jitter: {max_jitter_ms:.2f}ms)"
    )

    try:
        with Live(
            refresh_per_second=1,
            console=console,
            transient=False,
        ) as live:
            while time.monotonic() < end_time:
                try:
                    resp = httpx.get(base_url, timeout=2.0)
                    resp.raise_for_status()
                    streams = resp.json()
                except httpx.HTTPError as e:
                    console.print(f"[red]API error:[/red] {e}")
                    time.sleep(1.0)
                    continue

                receivers = [s for s in streams if s.get("role") == "receiver"]
                if stream_id:
                    receivers = [
                        s for s in receivers if s.get("stream_id") == stream_id
                    ]

                if not receivers:
                    live.update(
                        Table(title="[yellow]No active receiver streams[/yellow]")
                    )
                    time.sleep(1.0)
                    continue

                stream = receivers[0]
                if first_snapshot is None:
                    first_snapshot = stream
                last_snapshot = stream

                live.update(_make_table(stream))
                time.sleep(1.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted by user[/yellow]")

    # Summary
    if first_snapshot is None or last_snapshot is None:
        console.print("\n[red]No data collected[/red]")
        return

    console.print("\n[cyan]=== Verification Summary ===[/cyan]")

    expected_pps = 1000.0  # 1ms packet time
    packets_delta = (
        last_snapshot["packets_received"] - first_snapshot["packets_received"]
    )
    time_delta = last_snapshot["uptime_seconds"] - first_snapshot["uptime_seconds"]
    expected_packets = int(expected_pps * time_delta)
    loss_rate = (
        max(0, expected_packets - packets_delta) / expected_packets
        if expected_packets > 0
        else 0.0
    )

    jitter = last_snapshot.get("jitter", {}) or {}
    jitter_stddev = jitter.get("stddev_ms") or 0.0
    jitter_max = jitter.get("max_ms") or 0.0
    seq_gaps_delta = last_snapshot["sequence_gaps"] - first_snapshot["sequence_gaps"]
    ver_errors_delta = last_snapshot.get("verification_errors", 0) - first_snapshot.get(
        "verification_errors", 0
    )

    drift_ppm = _compute_drift_ppm(first_snapshot, last_snapshot)

    summary = Table(title="Results")
    summary.add_column("Check", style="cyan")
    summary.add_column("Value", style="green")
    summary.add_column("Threshold")
    summary.add_column("Result")

    def check(name: str, value: str, threshold: str, passed: bool) -> None:
        summary.add_row(
            name,
            value,
            threshold,
            "[green]PASS[/green]" if passed else "[red]FAIL[/red]",
        )

    loss_ok = loss_rate <= max_loss
    check(
        "Loss rate",
        f"{loss_rate * 100:.4f}%",
        f"<= {max_loss * 100:.4f}%",
        loss_ok,
    )

    jitter_stddev_ok = jitter_stddev <= max_jitter_stddev_ms
    check(
        "Jitter stddev",
        f"{jitter_stddev:.3f} ms",
        f"<= {max_jitter_stddev_ms:.2f} ms",
        jitter_stddev_ok,
    )

    jitter_peak_ok = jitter_max <= max_jitter_ms
    check(
        "Jitter peak",
        f"{jitter_max:.3f} ms",
        f"<= {max_jitter_ms:.2f} ms",
        jitter_peak_ok,
    )

    seq_ok = seq_gaps_delta == 0
    check(
        "Sequence gaps",
        str(seq_gaps_delta),
        "== 0",
        seq_ok,
    )

    ver_ok = ver_errors_delta == 0
    check(
        "Verification errors",
        str(ver_errors_delta),
        "== 0",
        ver_ok,
    )

    if drift_ppm is not None:
        drift_ok = abs(drift_ppm) < 100
        check(
            "Clock drift",
            f"{drift_ppm:+.1f} PPM",
            "< 100 PPM",
            drift_ok,
        )
    else:
        summary.add_row(
            "Clock drift",
            "n/a (enable --verify on connect)",
            "< 100 PPM",
            "[yellow]SKIP[/yellow]",
        )
        drift_ok = True

    console.print(summary)

    all_passed = (
        loss_ok
        and jitter_stddev_ok
        and jitter_peak_ok
        and seq_ok
        and ver_ok
        and drift_ok
    )

    if all_passed:
        console.print("\n[green bold]ALL CHECKS PASSED[/green bold]")
    else:
        console.print("\n[red bold]SOME CHECKS FAILED[/red bold]")
        raise click.exceptions.Exit(1)
