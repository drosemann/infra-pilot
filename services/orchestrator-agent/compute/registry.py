"""Provider registry — a plugin system for compute back-ends.

Providers self-register via the ``@provider`` decorator or by
calling ``ProviderRegistry.register()``.  Selection is done by name
so that manifests can specify ``provider: docker``, ``provider: proxmox``,
etc. without the core knowing about specific implementations.
"""

import logging
from typing import Dict, List, Optional, Type

from .base import ComputeProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Global registry of available compute providers."""

    _providers: Dict[str, Type[ComputeProvider]] = {}
    _instances: Dict[str, ComputeProvider] = {}

    @classmethod
    def register(cls, provider_cls: Type[ComputeProvider]) -> Type[ComputeProvider]:
        """Register a provider class (also usable as a decorator)."""
        name = getattr(provider_cls, "name", None)
        if name is None:
            try:
                name = provider_cls().name
            except Exception:
                name = provider_cls.__name__.lower()
        if not isinstance(name, str) or not name:
            name = provider_cls.__name__.lower()
        if name in cls._providers:
            logger.warning("Overwriting existing provider: %s", name)
        cls._providers[name] = provider_cls
        logger.info("Registered compute provider: %s (%s)", name, provider_cls.__name__)
        return provider_cls

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Return True when a provider with ``name`` is registered."""
        return name in cls._providers

    @classmethod
    def names(cls) -> List[str]:
        """Return the sorted list of registered provider names."""
        return sorted(cls._providers)

    @classmethod
    def get(cls, name: str, **kwargs) -> Optional[ComputeProvider]:
        """Return a singleton provider instance by name.

        The instance is cached after the first successful construction, so
        later ``kwargs`` are ignored; pass constructor options on the first
        call (or clear the cache in tests).
        """
        if name in cls._instances:
            return cls._instances[name]
        provider_cls = cls._providers.get(name)
        if not provider_cls:
            logger.error(
                "Unknown compute provider: %s (available: %s)",
                name,
                list(cls._providers),
            )
            return None
        try:
            instance = provider_cls(**kwargs)
            cls._instances[name] = instance
            return instance
        except Exception as exc:
            logger.error("Failed to instantiate provider %s: %s", name, exc)
            return None

    @classmethod
    def get_or_default(
        cls, name: Optional[str], default: str = "docker", **kwargs
    ) -> Optional[ComputeProvider]:
        """Return provider ``name`` or fall back to ``default``.

        Used when a manifest omits ``provider``: the platform default keeps
        working even if the requested backend is not registered in this
        deployment.  Returns ``None`` only when neither is available.
        """
        if name:
            provider_instance = cls.get(name, **kwargs)
            if provider_instance is not None:
                return provider_instance
            logger.warning("Provider %s unavailable; falling back to %s", name, default)
        return cls.get(default, **kwargs)

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """Return ``{name: qualname}`` for every registered provider."""
        return {
            n: f"{c.__module__}.{c.__qualname__}" for n, c in cls._providers.items()
        }

    @classmethod
    def list_capabilities(cls) -> Dict[str, Dict[str, object]]:
        """Return ``{name: capabilities}`` for instantiable providers.

        A provider that needs an optional dependency or live credentials
        may fail to instantiate; it is reported with an ``error`` entry
        instead of being omitted so operators can see the misconfiguration.
        """
        result: Dict[str, Dict[str, object]] = {}
        for name in cls.names():
            instance = cls.get(name)
            if instance is None:
                result[name] = {"error": "provider failed to initialize"}
                continue
            caps = getattr(instance, "capabilities", None)
            try:
                result[name] = caps.as_dict() if caps else {}
            except Exception as exc:  # pragma: no cover - defensive
                result[name] = {"error": str(exc)}
        return result

    @classmethod
    def clear(cls) -> None:
        """Reset registry (useful in tests)."""
        cls._providers.clear()
        cls._instances.clear()

    @classmethod
    def clear_instances(cls) -> None:
        """Drop cached provider singletons but keep registrations.

        Tests that mutate environment variables between cases use this so a
        provider rebuilt with new configuration is actually re-instantiated.
        """
        cls._instances.clear()


provider = ProviderRegistry.register
