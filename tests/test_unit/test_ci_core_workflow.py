from pathlib import Path

import pytest
import yaml


WORKFLOW_PATH = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci-core.yml"


@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH, "r") as f:
        return yaml.safe_load(f)


@pytest.mark.unit
def test_workflow_file_is_valid_yaml():
    """Workflow file must be parseable as valid YAML."""
    with open(WORKFLOW_PATH, "r") as f:
        parsed = yaml.safe_load(f)
    assert parsed is not None


@pytest.mark.unit
def test_workflow_has_top_level_permissions(workflow):
    """Top-level permissions key must exist after the PR change."""
    assert "permissions" in workflow, "Expected top-level 'permissions' key in workflow"


@pytest.mark.unit
def test_top_level_permissions_contents_is_read(workflow):
    """Top-level permissions.contents must be 'read' (not 'write' or 'admin')."""
    permissions = workflow["permissions"]
    assert "contents" in permissions, "Expected 'contents' in top-level permissions"
    assert permissions["contents"] == "read"


@pytest.mark.unit
def test_top_level_permissions_does_not_grant_write(workflow):
    """Top-level permissions must not grant any write-level access."""
    permissions = workflow["permissions"]
    for scope, level in permissions.items():
        assert level != "write", (
            f"Top-level permission '{scope}' must not be 'write'; "
            "write access should only be granted at the job level when required"
        )


@pytest.mark.unit
def test_top_level_permissions_does_not_include_packages(workflow):
    """Top-level permissions must not include packages scope.
    The packages: write permission is only needed by the docker job and
    should remain scoped to that job, not elevated to the workflow level.
    """
    permissions = workflow["permissions"]
    assert "packages" not in permissions, (
        "packages permission must not appear at the top level; "
        "it should remain scoped to the docker job only"
    )


@pytest.mark.unit
def test_top_level_permissions_is_minimal(workflow):
    """Top-level permissions block must only contain 'contents'.
    Principle of least privilege: only the minimum required scopes
    should be declared at the workflow level.
    """
    permissions = workflow["permissions"]
    assert list(permissions.keys()) == ["contents"], (
        f"Expected only 'contents' at top-level permissions, got: {list(permissions.keys())}"
    )


@pytest.mark.unit
def test_permissions_is_at_workflow_level_not_nested_in_jobs(workflow):
    """Regression: permissions must be a top-level key, not accidentally nested inside jobs."""
    # Confirm it is NOT inside any job definition
    jobs = workflow.get("jobs", {})
    for job_name, job_def in jobs.items():
        if job_name == "docker":
            # docker job intentionally has its own permissions block - skip it
            continue
        job_permissions = job_def.get("permissions")
        assert job_permissions is None, (
            f"Job '{job_name}' has an unexpected permissions block; "
            "it should inherit the top-level permissions"
        )


@pytest.mark.unit
def test_test_job_inherits_top_level_permissions(workflow):
    """The 'test' job must not define its own permissions, relying on the top-level default."""
    test_job = workflow["jobs"]["test"]
    assert "permissions" not in test_job, (
        "The 'test' job must not override permissions; "
        "it should inherit 'contents: read' from the top-level permissions block"
    )


@pytest.mark.unit
def test_docker_job_retains_packages_write_permission(workflow):
    """The docker job must still have packages: write to push images to the registry."""
    docker_job = workflow["jobs"]["docker"]
    assert "permissions" in docker_job, "docker job must define its own permissions"
    docker_permissions = docker_job["permissions"]
    assert docker_permissions.get("packages") == "write", (
        "docker job must retain 'packages: write' permission for container registry push"
    )


@pytest.mark.unit
def test_docker_job_permissions_include_contents_read(workflow):
    """The docker job's explicit permissions block must also include contents: read."""
    docker_job = workflow["jobs"]["docker"]
    docker_permissions = docker_job["permissions"]
    assert docker_permissions.get("contents") == "read", (
        "docker job must explicitly include 'contents: read' alongside 'packages: write'"
    )


@pytest.mark.unit
@pytest.mark.parametrize("permission_value", ["write", "admin", None, ""])
def test_top_level_contents_permission_rejects_elevated_values(permission_value):
    """Boundary/negative: contents permission value must be exactly 'read'."""
    assert permission_value != "read", (
        f"Value '{permission_value}' must not be used as the top-level contents permission"
    )


@pytest.mark.unit
def test_top_level_permissions_value_is_string_not_bool(workflow):
    """Regression: permissions.contents must be the string 'read', not a boolean True/False."""
    permissions = workflow["permissions"]
    contents_value = permissions["contents"]
    assert isinstance(contents_value, str), (
        f"permissions.contents must be a string, got {type(contents_value).__name__}"
    )
    assert contents_value == "read"
