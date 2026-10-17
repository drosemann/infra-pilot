"""Runbooks - Operational runbook CRUD, execution, and history."""

import builtins
import json
import time
from typing import Any, Dict, Optional

import typer
import yaml

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Operational runbooks",
    epilog=(
        "Examples:\n\n"
        "  ipilot runbooks list\n"
        "  ipilot runbooks show builtin-deploy-prod\n"
        "  ipilot runbooks create --file runbook.yaml\n"
        "  ipilot runbooks edit r1 --name new-name\n"
        "  ipilot runbooks execute r1 --wait --timeout 120\n"
        "  ipilot runbooks execute r1 --dry-run\n"
        "  ipilot runbooks history --runbook r1\n"
        "  ipilot runbooks validate --file runbook.yaml\n"
        "  ipilot runbooks export builtin-deploy-prod --format yaml\n"
    ),
)

TERMINAL_STATUSES = {"executed", "success", "failed", "error", "completed", "cancelled"}
POLL_INTERVAL_SECONDS = 1.0


# A runbook that only exists in someone's head is a incident waiting to happen.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _as_list(result):
    if isinstance(result, builtins.list):
        return result
    if isinstance(result, dict) and isinstance(result.get("runbooks"), builtins.list):
        return result["runbooks"]
    return result


def _load_runbook_file(path: str) -> Dict[str, Any]:
    """Load a runbook definition from a YAML or JSON file.

    Args:
        path: Path to the file.

    Returns:
        The parsed definition dict.

    Raises:
        typer.Exit: If the file is unreadable or malformed.
    """
    try:
        with open(path) as handle:
            data = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError, json.JSONDecodeError) as exc:
        typer.echo(f"Error loading runbook file: {exc}", err=True)
        raise typer.Exit(code=1)
    if not isinstance(data, dict):
        typer.echo(f"Error: {path} must contain a mapping with name and steps", err=True)
        raise typer.Exit(code=1)
    return data


def _find_runbook(client: ApiClient, runbook_id: str) -> Any:
    """Find a runbook by ID or name in the list endpoint.

    Args:
        client: API client.
        runbook_id: Runbook ID or name.

    Returns:
        The runbook dict, or None if not found / on error.
    """
    result = client.list_runbooks()
    runbooks = _as_list(result)
    if isinstance(runbooks, builtins.list):
        for runbook in runbooks:
            if not isinstance(runbook, dict):
                continue
            if str(runbook.get("id")) == runbook_id or runbook.get("name") == runbook_id:
                return runbook
    return None


@app.command("list")
def list_cmd(ctx: typer.Context):
    """List runbooks (built-in and user-defined).

    Built-in runbooks (deploy-production, rollback-deployment,
    backup-verify, system-update) are merged with user-defined ones.
    """
    client = _get_client(ctx)
    result = client.list_runbooks()
    print_output(_as_list(result), ctx.obj.get("output", "table"))


@app.command()
def show(
    ctx: typer.Context,
    runbook_id: str = typer.Argument(..., help="Runbook ID or name"),
):
    """Show a runbook's definition and steps.

    Accepts either the runbook ID or its name.
    """
    client = _get_client(ctx)
    runbook = _find_runbook(client, runbook_id)
    if runbook is None:
        print_output({"error": f"Runbook {runbook_id} not found"}, ctx.obj.get("output", "table"))
        return
    print_output(runbook, ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    file: str = typer.Option(..., "--file", "-f", help="YAML or JSON runbook definition"),
):
    """Create a runbook from a YAML/JSON definition file.

    The file must be a mapping with a non-empty `name` and a
    `steps` list; each step is a mapping (action/target, etc.).
    """
    data = _load_runbook_file(file)
    name = data.get("name")
    steps = data.get("steps")
    if not name or not isinstance(steps, list) or not steps:
        typer.echo(f"Error: {file} must define 'name' and a non-empty 'steps' list", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.create_runbook(
        name=name,
        description=data.get("description", ""),
        steps=[dict(step) for step in steps if isinstance(step, dict)],
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def edit(
    ctx: typer.Context,
    runbook_id: str = typer.Argument(..., help="Runbook ID"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="YAML or JSON with new name/description/steps"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New runbook name"),
    description: Optional[str] = typer.Option(None, "--description", help="New description"),
):
    """Edit an existing runbook.

    Pass --file for a full replacement of name/description/steps,
    or --name/--description for targeted changes. At least one
    field is required.
    """
    fields: Dict[str, Any] = {}
    if file:
        data = _load_runbook_file(file)
        for key in ("name", "description", "steps"):
            if key in data:
                fields[key] = data[key]
    if name is not None:
        fields["name"] = name
    if description is not None:
        fields["description"] = description
    if not fields:
        typer.echo("Error: provide --file, --name, or --description", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.update_runbook(
        runbook_id,
        name=fields.get("name"),
        description=fields.get("description"),
        steps=fields.get("steps"),
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def delete(
    ctx: typer.Context,
    runbook_id: str = typer.Argument(..., help="Runbook ID"),
):
    """Delete a runbook.

    Removes the runbook; past executions remain in history.
    """
    client = _get_client(ctx)
    result = client.delete_runbook(runbook_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def execute(
    ctx: typer.Context,
    runbook_id: str = typer.Argument(..., help="Runbook ID"),
    wait: bool = typer.Option(False, "--wait", help="Poll until the execution reaches a terminal status"),
    timeout: int = typer.Option(300, "--timeout", help="Seconds to wait with --wait"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the steps that would run without executing"),
):
    """Execute a runbook.

    --wait polls the execution until it reaches a terminal status
    (or --timeout seconds elapse). --dry-run prints the steps that
    would run without executing anything.
    """
    client = _get_client(ctx)
    if dry_run:
        runbook = _find_runbook(client, runbook_id)
        if runbook is None:
            print_output({"error": f"Runbook {runbook_id} not found"}, ctx.obj.get("output", "table"))
            return
        print_output(
            {"dry_run": True, "id": runbook.get("id"), "name": runbook.get("name"), "steps": runbook.get("steps", [])},
            ctx.obj.get("output", "table"),
        )
        return
    result = client.execute_runbook(runbook_id)
    if wait and isinstance(result, dict) and "error" not in result:
        deadline = time.monotonic() + timeout
        execution_id = result.get("execution_id")
        while (
            result.get("status") not in TERMINAL_STATUSES
            and execution_id
            and time.monotonic() < deadline
        ):
            time.sleep(POLL_INTERVAL_SECONDS)
            result = client.get_runbook_execution(str(execution_id))
            if not isinstance(result, dict) or "error" in result:
                break
        if isinstance(result, dict) and result.get("status") not in TERMINAL_STATUSES:
            typer.echo(
                f"Warning: execution {execution_id} did not reach a terminal status "
                f"within {timeout}s",
                err=True,
            )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def history(
    ctx: typer.Context,
    runbook_id: Optional[str] = typer.Option(None, "--runbook", help="Filter by runbook ID"),
):
    """List runbook execution history.

    Optionally filter by --runbook ID.
    """
    client = _get_client(ctx)
    result = client.list_runbook_executions(runbook_id=runbook_id)
    data = result if isinstance(result, builtins.list) else result.get("executions", result)
    print_output(data, ctx.obj.get("output", "table"))


@app.command("execution")
def execution_status(
    ctx: typer.Context,
    execution_id: str = typer.Argument(..., help="Execution ID"),
):
    """Show the status of a single runbook execution.

    Use the execution_id returned by `execute` to follow up on a
    run that was started without --wait.
    """
    client = _get_client(ctx)
    result = client.get_runbook_execution(execution_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command("steps")
def list_steps(
    ctx: typer.Context,
    runbook_id: str = typer.Argument(..., help="Runbook ID or name"),
):
    """List the steps of a runbook.

    Accepts the runbook ID or name; prints just the step list.
    """
    client = _get_client(ctx)
    runbook = _find_runbook(client, runbook_id)
    if runbook is None:
        print_output({"error": f"Runbook {runbook_id} not found"}, ctx.obj.get("output", "table"))
        return
    print_output(runbook.get("steps", []), ctx.obj.get("output", "table"))


@app.command()
def validate(
    ctx: typer.Context,
    file: str = typer.Option(..., "--file", "-f", help="YAML or JSON runbook definition"),
):
    """Validate a runbook definition file without creating it.

    Checks that the file parses, is a mapping, defines a non-empty
    `name`, and has a `steps` list of mappings -- the same rules
    `create` enforces. Exits 0 on success, 2 on invalid definition.
    Does not contact the backend.
    """
    data = _load_runbook_file(file)
    problems = []
    name = data.get("name")
    if not name or not isinstance(name, str):
        problems.append("'name' must be a non-empty string")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        problems.append("'steps' must be a non-empty list")
    else:
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                problems.append(f"step {index} must be a mapping")
            elif not step:
                problems.append(f"step {index} is empty")
    if "description" in data and data["description"] is not None and not isinstance(data["description"], str):
        problems.append("'description' must be a string")
    if problems:
        for problem in problems:
            typer.echo(f"Error: {problem}", err=True)
        raise typer.Exit(code=2)
    typer.echo(f"OK: {file} defines runbook {name!r} with {len(steps)} step(s)")


@app.command()
def export(
    ctx: typer.Context,
    runbook_id: str = typer.Argument(..., help="Runbook ID or name"),
    fmt: str = typer.Option("yaml", "--format", "-f", help="Output format: yaml or json"),
    output_file: Optional[str] = typer.Option(None, "--file", "-o", help="Write to file instead of stdout"),
):
    """Export a runbook definition to YAML or JSON.

    Fetches the runbook from the panel (list endpoint) and writes a
    definition file suitable for `runbooks create --file`, so a
    runbook can be duplicated or version-controlled outside the panel.
    """
    if fmt not in ("yaml", "json"):
        typer.echo("Error: --format must be yaml or json", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    runbook = _find_runbook(client, runbook_id)
    if runbook is None:
        print_output({"error": f"Runbook {runbook_id} not found"}, ctx.obj.get("output", "table"))
        raise typer.Exit(code=1)
    definition = {
        "name": runbook.get("name"),
        "description": runbook.get("description", ""),
        "steps": runbook.get("steps", []),
    }
    if fmt == "json":
        text = json.dumps(definition, indent=2, default=str)
    else:
        text = yaml.safe_dump(definition, sort_keys=False, default_flow_style=False)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as handle:
            handle.write(text)
        typer.echo(f"Exported {definition['name']!r} to {output_file}")
        return
    typer.echo(text, nl=False)
