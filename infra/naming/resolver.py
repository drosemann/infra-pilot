import os
from pathlib import Path
import yaml

# Paths to maps
_BASE_MAP_PATH = Path(__file__).parent / "provider_map.yaml"
_OVERRIDES_ENV_PATH = None  # can be overridden by PROVIDER_CONFIG_OVERRIDE env var

def _load_base_map() -> dict:
    if not _BASE_MAP_PATH.exists():
        return {}
    with open(_BASE_MAP_PATH, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except Exception:
            return {}

def _load_overrides_from_path(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except Exception:
            return {}

def _default_overrides_path() -> Path:
    base = Path(__file__).parent / ".." / "overrides" / "provider_map.yaml"
    # Normalize path
    return base.resolve()

def _merge_maps(base: dict, overrides: dict) -> dict:
    # Simple shallow merge: keys in overrides take precedence
    merged = dict(base or {})
    for k, v in (overrides or {}).items():
        merged[k] = v
    return merged

def load_map() -> dict:
    base = _load_base_map()
    # Resolve override path from env var if set, else default location
    override_path = None
    env_path = os.environ.get("PROVIDER_CONFIG_OVERRIDE")
    if env_path:
        override_path = Path(env_path)
    else:
        override_path = _default_overrides_path()
    overrides = _load_overrides_from_path(override_path)
    return _merge_maps(base, overrides)

_MAP = load_map()

def refresh_map():
    global _MAP
    _MAP = load_map()

def resolve_provider(token: str) -> str:
    """Resolve a neutral token to its concrete provider identity.

    If the token is not present in the map, a best-effort fallback is returned
    (the token itself).
    """
    if not token:
        return token
    return _MAP.get(token, token)

def current_env() -> str:
    """Return the current test environment label.

    Looks for TEST_ENV env var; defaults to 'local'.
    """
    return os.environ.get("TEST_ENV", "local")
