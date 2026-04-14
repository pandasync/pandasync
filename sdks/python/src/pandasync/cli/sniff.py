"""pandasync sniff -- capture packets and verify the audio payload."""

from __future__ import annotations

import math
import socket
import struct
import time

import click
from rich.console import Console
from rich.table import Table


def _goertzel(samples: list[float], target_freq: float, sample_rate: int) -> float:
    """Compute the magnitude of target_freq in samples using Goertzel algorithm.

    Returns the magnitude (not normalized). Pure Python, no numpy needed.
    """
    n = len(samples)
    k = int(0.5 + (n * target_freq) / sample_rate)
    w = 2.0 * math.pi * k / n
    cosine = math.cos(w)
    coeff = 2.0 * cosine

    s_prev = 0.0
    s_prev2 = 0.0
    for x in samples:
        s = x + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s
    magnitude = math.sqrt(
        s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
    )
    return magnitude


def _estimate_dominant_frequency(
    samples: list[float],
    sample_rate: int,
    candidates: list[float],
) -> tuple[float, float]:
    """Return (freq, magnitude) of the strongest candidate frequency."""
    best_freq = candidates[0]
    best_mag = 0.0
    for f in candidates:
        mag = _goertzel(samples, f, sample_rate)
        if mag > best_mag:
            best_mag = mag
            best_freq = f
    return best_freq, best_mag


def _decode_l24(payload: bytes, count: int) -> list[float]:
    """Decode big-endian 24-bit PCM to float samples in [-1, 1]."""
    samples = []
    for i in range(count):
        offset = i * 3
        if offset + 3 > len(payload):
            break
        b0, b1, b2 = payload[offset], payload[offset + 1], payload[offset + 2]
        val = (b0 << 16) | (b1 << 8) | b2
        if val >= 0x800000:
            val -= 0x1000000
        samples.append(val / 0x7FFFFF)
    return samples


@click.command()
@click.option(
    "--port",
    "-p",
    default=5004,
    type=int,
    help="UDP port to capture on.",
)
@click.option(
    "--packets",
    "-n",
    default=1000,
    type=int,
    help="Number of packets to capture.",
)
@click.option(
    "--sample-rate",
    default=48000,
    type=int,
    help="Expected sample rate.",
)
@click.option(
    "--samples-per-packet",
    default=48,
    type=int,
    help="Expected PCM samples per packet.",
)
@click.option(
    "--expected-freq",
    default=440.0,
    type=float,
    help="Expected tone frequency in Hz.",
)
@click.option(
    "--verification",
    is_flag=True,
    help="Expect a verification header in the first 12 bytes of payload.",
)
def sniff(
    port: int,
    packets: int,
    sample_rate: int,
    samples_per_packet: int,
    expected_freq: float,
    verification: bool,
) -> None:
    """Capture RTP packets and verify the audio payload.

    Binds to PORT (default 5004), captures PACKETS packets, decodes the
    24-bit PCM payload, and runs a Goertzel analysis at the expected
    frequency. Reports dominant frequency, peak/RMS, and any issues.

    Note: only one process can bind to a given UDP port at a time.
    Stop any active receiver on the same port before running sniff.
    """
    console = Console()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", port))
    except OSError as e:
        console.print(f"[red]Failed to bind port {port}: {e}[/red]")
        console.print("If a PandaSync receiver is bound to this port, stop it first.")
        return

    sock.settimeout(3.0)

    all_samples: list[float] = []
    packet_count = 0
    invalid_packets = 0
    peer = None
    first_seq: int | None = None
    last_seq: int | None = None
    seq_gaps = 0
    first_counter: int | None = None
    last_counter: int | None = None
    counter_errors = 0
    arrival_times: list[float] = []

    console.print(f"[cyan]Capturing {packets} packets on port {port}...[/cyan]")
    start = time.monotonic()

    try:
        while packet_count < packets:
            try:
                data, addr = sock.recvfrom(65535)
            except TimeoutError:
                console.print(
                    "[yellow]Timeout waiting for packets. Is a sender running?[/yellow]"
                )
                break

            arrival_times.append(time.monotonic())

            if len(data) < 12:
                invalid_packets += 1
                continue

            peer = addr
            try:
                _, _, seq, _, _ = struct.unpack("!BBHII", data[:12])
            except struct.error:
                invalid_packets += 1
                continue

            if first_seq is None:
                first_seq = seq
            if last_seq is not None:
                expected = (last_seq + 1) & 0xFFFF
                if seq != expected:
                    diff = (seq - expected) & 0xFFFF
                    if 0 < diff < 32768:
                        seq_gaps += diff
            last_seq = seq

            payload = data[12:]

            # If verification header is expected, skip the first 12 bytes
            # and parse the counter
            audio_start = 0
            if verification and len(payload) >= 12:
                try:
                    counter, _send_time_ns = struct.unpack("!IQ", payload[:12])
                    if first_counter is None:
                        first_counter = counter
                    if last_counter is not None:
                        expected_counter = (last_counter + 1) & 0xFFFFFFFF
                        if counter != expected_counter:
                            counter_errors += 1
                    last_counter = counter
                    audio_start = 12
                except struct.error:
                    pass

            audio_bytes = payload[audio_start:]
            samples = _decode_l24(
                audio_bytes,
                min(samples_per_packet, len(audio_bytes) // 3),
            )
            all_samples.extend(samples)
            packet_count += 1
    finally:
        sock.close()

    elapsed = time.monotonic() - start

    if packet_count == 0:
        console.print("[red]No packets captured.[/red]")
        return

    # Analyze audio
    peak = max(abs(s) for s in all_samples)
    rms = math.sqrt(sum(s * s for s in all_samples) / len(all_samples))

    # Frequency estimation: test candidates near expected
    candidates = [
        expected_freq - 10,
        expected_freq - 1,
        expected_freq,
        expected_freq + 1,
        expected_freq + 10,
    ]
    # Use up to 4800 samples for FFT (100ms at 48k)
    analysis_samples = all_samples[: min(4800, len(all_samples))]
    est_freq, est_mag = _estimate_dominant_frequency(
        analysis_samples, sample_rate, candidates
    )

    # Render results
    table = Table(title="Sniff Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Peer", f"{peer[0]}:{peer[1]}" if peer else "n/a")
    table.add_row("Packets captured", str(packet_count))
    table.add_row("Invalid packets", str(invalid_packets))
    table.add_row("Capture duration", f"{elapsed:.2f}s")
    table.add_row("Packets/sec", f"{packet_count / elapsed:.1f}")
    table.add_row("Total samples", str(len(all_samples)))
    table.add_row("Peak amplitude", f"{peak:.4f}")
    table.add_row("RMS amplitude", f"{rms:.4f}")
    table.add_row(
        "Peak dB (full-scale)",
        f"{20 * math.log10(peak) if peak > 0 else -math.inf:.1f} dB",
    )
    table.add_row(
        "RMS dB (full-scale)",
        f"{20 * math.log10(rms) if rms > 0 else -math.inf:.1f} dB",
    )
    table.add_row("Estimated frequency", f"{est_freq:.1f} Hz")
    table.add_row("Expected frequency", f"{expected_freq:.1f} Hz")
    table.add_row("RTP sequence gaps", str(seq_gaps))
    if verification:
        table.add_row("Counter errors", str(counter_errors))

    console.print(table)

    # Summary
    issues = []
    if invalid_packets > 0:
        issues.append(f"{invalid_packets} invalid packets")
    if seq_gaps > 0:
        issues.append(f"{seq_gaps} sequence gaps")
    if verification and counter_errors > 0:
        issues.append(f"{counter_errors} verification errors")
    if abs(est_freq - expected_freq) > 2:
        issues.append(f"frequency mismatch ({est_freq:.1f} vs {expected_freq:.1f})")
    if peak < 0.01:
        issues.append("signal too quiet")

    if issues:
        console.print(f"\n[red]Issues:[/red] {', '.join(issues)}")
        raise click.exceptions.Exit(1)
    else:
        console.print("\n[green bold]Payload looks healthy.[/green bold]")
