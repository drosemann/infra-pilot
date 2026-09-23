import builtins

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(help="Server management")


def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


@app.command()
def list(
    ctx: typer.Context,
    output: str = typer.Option(None, "--output", "-o", help="Output format"),
) -> None:
    """List all servers

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    client = _get_client(ctx)
    result = client.list_servers()
    data = (
        result if isinstance(result, builtins.list) else result.get("servers", result)
    )
    print_output(data, output or ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Server name"),
    image: str = typer.Option(
        None, "--image", help="Docker image (e.g. nginx:latest)"
    ),
    server_type: str = typer.Option(
        None, "--type", "-t", help="Deprecated alias for --image"
    ),
    memory: int = typer.Option(None, "--memory", "-m", help="Memory in MB"),
) -> None:
    """Create a new server

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    actual_image = image or server_type
    if not actual_image:
        typer.echo("Missing option '--image' / '--type'.", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.create_server(name, actual_image, memory)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def delete(
    ctx: typer.Context,
    server: str = typer.Argument(..., help="Server ID or name"),
) -> None:
    """Delete a server

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    client = _get_client(ctx)
    result = client.delete_server(server)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def status(
    ctx: typer.Context,
    server: str = typer.Argument(..., help="Server ID or name"),
) -> None:
    """Get server status

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    client = _get_client(ctx)
    result = client.server_status(server)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def start(
    ctx: typer.Context,
    server: str = typer.Argument(..., help="Server ID or name"),
) -> None:
    """Start a stopped server container

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    client = _get_client(ctx)
    result = client.start_server(server)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def stop(
    ctx: typer.Context,
    server: str = typer.Argument(..., help="Server ID or name"),
) -> None:
    """Stop a running server container

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    client = _get_client(ctx)
    result = client.stop_server(server)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def restart(
    ctx: typer.Context,
    server: str = typer.Argument(..., help="Server ID or name"),
) -> None:
    """Restart a server container

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    client = _get_client(ctx)
    result = client.restart_server(server)
    print_output(result, ctx.obj.get("output", "table"))
