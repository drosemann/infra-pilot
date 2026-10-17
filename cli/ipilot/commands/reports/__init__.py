"""Reports - On-demand usage reports, exports, and scheduling."""

import sys
from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Usage reports",
    epilog=(
        "Examples:\n\n"
        "  ipilot reports generate\n"
        "  ipilot reports generate --start 2026-01-01 --end 2026-02-01\n"
        "  ipilot reports download --format csv --file report.csv\n"
        "  ipilot reports download --format pdf > report.pdf\n"
        "  ipilot reports schedule --frequency weekly\n"
    ),
)

REPORT_FORMATS = ("csv", "pdf", "json")
FREQUENCIES = ("daily", "weekly")


# The panel computes reports on demand; there is no stored report list.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


@app.command("generate")
def generate(
    ctx: typer.Context,
    start: Optional[str] = typer.Option(None, "--start", help="ISO-8601 period start"),
    end: Optional[str] = typer.Option(None, "--end", help="ISO-8601 period end"),
):
    """Generate a usage report for a period (default: latest data).

    The panel computes the report on demand from live data; there is
    no stored report list. --start/--end bound the period.
    """
    client = _get_client(ctx)
    result = client.get_report(start_date=start, end_date=end)
    print_output(result, ctx.obj.get("output", "table"))


@app.command("list")
def list_cmd(
    ctx: typer.Context,
    start: Optional[str] = typer.Option(None, "--start", help="ISO-8601 period start"),
    end: Optional[str] = typer.Option(None, "--end", help="ISO-8601 period end"),
):
    """Show the report for a period (alias for generate).

    Kept for symmetry with other list subcommands; prints the same
    computed report as `generate`.
    """
    client = _get_client(ctx)
    result = client.get_report(start_date=start, end_date=end)
    print_output(result, ctx.obj.get("output", "table"))


@app.command("download")
def download(
    ctx: typer.Context,
    fmt: str = typer.Option("csv", "--format", "-f", help=f"Export format: {', '.join(REPORT_FORMATS)}"),
    output_file: Optional[str] = typer.Option(None, "--file", help="Write to file instead of stdout"),
    start: Optional[str] = typer.Option(None, "--start", help="ISO-8601 period start"),
    end: Optional[str] = typer.Option(None, "--end", help="ISO-8601 period end"),
):
    """Download a report in CSV, PDF, or JSON format.

    Streams the export to stdout unless --file is given. Use
    --start/--end to bound the reporting period.
    """
    if fmt not in REPORT_FORMATS:
        typer.echo(
            f"Error: unsupported format '{fmt}' (choose from {', '.join(REPORT_FORMATS)})",
            err=True,
        )
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.download_report(fmt=fmt, start_date=start, end_date=end)
    if not isinstance(result, dict) or "error" in result:
        message = result.get("error") if isinstance(result, dict) else "Unexpected response"
        typer.echo(f"Error: {message}", err=True)
        raise typer.Exit(code=1)
    content = result.get("content", "")
    if output_file:
        with open(output_file, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        typer.echo(f"Report written to {output_file}")
        return
    sys.stdout.write(content)
    if content and not content.endswith("\n"):
        sys.stdout.write("\n")


@app.command()
def schedule(
    ctx: typer.Context,
    frequency: str = typer.Option("daily", "--frequency", help=f"Recurrence: {', '.join(FREQUENCIES)}"),
):
    """Schedule a recurring report.

    --frequency is daily or weekly. Note: some panel builds do not
    yet implement the schedules endpoint; failures surface a clear
    backend error.
    """
    if frequency not in FREQUENCIES:
        typer.echo(
            f"Error: unsupported frequency '{frequency}' (choose from {', '.join(FREQUENCIES)})",
            err=True,
        )
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.create_report_schedule(frequency=frequency)
    print_output(result, ctx.obj.get("output", "table"))
