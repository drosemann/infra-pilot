"""Compute provider abstraction layer.

Plug in any hypervisor or cloud provider behind a unified interface.
"""

from .base import (
    ComputeProvider,
    InstanceAlreadyExistsError,
    InstanceNotFoundError,
    ProviderAuthError,
    ProviderCapabilities,
    ProviderConfigError,
    ProviderConflictError,
    ProviderError,
    ProviderNotSupportedError,
    ProviderPermissionError,
    ProviderUnavailableError,
)
from .registry import ProviderRegistry

__all__ = [
    "ComputeProvider",
    "InstanceAlreadyExistsError",
    "InstanceNotFoundError",
    "ProviderAuthError",
    "ProviderCapabilities",
    "ProviderConfigError",
    "ProviderConflictError",
    "ProviderError",
    "ProviderNotSupportedError",
    "ProviderPermissionError",
    "ProviderRegistry",
    "ProviderUnavailableError",
]
