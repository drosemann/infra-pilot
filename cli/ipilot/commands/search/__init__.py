"""Search - Global search across panel resources.

Wired as a top-level ``ipilot search`` command (not a sub-app group) so
options may follow the query term naturally.
"""

from typing import Any, Dict, List, Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

KNOWN_TYPES = ("app", "server", "backup", "runbook", "secret", "host", "audit")


# One query, six tables, zero excuses for duplicate rows.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _normalise(results: List[Any]) -> List[Dict[str, Any]]:
    """Normalise result rows to {type, id, title, subtitle} shape.

    The legacy /api/search endpoint returns {id, name, type}; map it to
    the richer global-search shape so callers see one schema.

    Args:
        results: Raw result rows.

    Returns:
        Normalised result dicts.
    """
    normalised = []
    for row in results:
        if not isinstance(row, dict):
            continue
        normalised.append(
            {
                "type": row.get("type"),
                "id": row.get("id"),
                "title": row.get("title", row.get("name")),
                "subtitle": row.get("subtitle", row.get("status")),
            }
        )
    return normalised


def _dedupe(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop duplicate (type, id) rows, preserving order.

    Args:
        results: Normalised result dicts.

    Returns:
        Deduplicated result dicts.
    """
    seen = set()
    deduped = []
    for row in results:
        key = (row.get("type"), str(row.get("id")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def run_search(
    ctx: typer.Context,
    query: str,
    type_filter: Optional[str] = None,
    limit: int = 50,
    types: Optional[List[str]] = None,
) -> None:
    """Run a global search and print the results.

    Uses /api/global-search and falls back to the legacy /api/search
    endpoint when the panel does not implement it. Results are
    normalised to a single {type, id, title, subtitle} schema and
    deduplicated by (type, id) before filtering.

    Args:
        ctx: Typer context (carries output format and profile).
        query: Search term (at least 2 characters).
        type_filter: Optional result type filter (app, server, backup,
            runbook, secret, host, audit).
        limit: Maximum results to print.
        types: Optional list of accepted result types; combined with
            type_filter when both are given.

    Raises:
        typer.Exit: On invalid input.
    """
    if len(query) < 2:
        typer.echo("Error: query must be at least 2 characters", err=True)
        raise typer.Exit(code=2)
    if limit < 1:
        typer.echo("Error: --limit must be at least 1", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.global_search(query)
    if isinstance(result, dict) and "error" in result:
        result = client.basic_search(query)
        if isinstance(result, dict) and "error" in result:
            print_output(result, ctx.obj.get("output", "table"))
            return
    raw = result.get("results", []) if isinstance(result, dict) else result
    results = _dedupe(_normalise(raw if isinstance(raw, list) else []))
    allowed = set(types or [])
    if type_filter:
        allowed.add(type_filter)
    if allowed:
        results = [r for r in results if r.get("type") in allowed]
    print_output(results[:limit], ctx.obj.get("output", "table"))
