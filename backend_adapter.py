"""Safe integration boundary for the existing VFD project.

Set VFD_BACKEND_ADAPTER=your_module:create_adapter and implement only thin
wrappers around the project's existing Python/C++ functions. No protocol logic
is reimplemented here.
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any


class BackendUnavailable(RuntimeError):
    """Raised when the existing project backend has not been connected."""


def load_spec(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load register definitions from the existing JSON specification."""
    configured = path or os.getenv("VFD_REGISTER_SPEC", "register_spec.json")
    spec_path = Path(configured).expanduser()
    if not spec_path.is_file():
        return []
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read register specification: {exc}") from exc
    return normalize_registers(raw)


def normalize_registers(raw: Any) -> list[dict[str, Any]]:
    """Normalize common JSON-spec layouts without supplying register data."""
    entries: Any = raw
    if isinstance(raw, dict):
        for key in ("registers", "holding_registers", "input_registers"):
            if key in raw:
                entries = raw[key]
                break
        else:
            # A mapping of address -> register definition is also supported.
            entries = [dict(value, address=value.get("address", key))
                       for key, value in raw.items() if isinstance(value, dict)]
    if isinstance(entries, dict):
        entries = [dict(value, address=value.get("address", key))
                   for key, value in entries.items() if isinstance(value, dict)]
    if not isinstance(entries, list):
        raise ValueError("Register specification must contain a list or address mapping.")

    normalized: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        address = item.get("address", item.get("register", item.get("id")))
        try:
            address = int(address)
        except (TypeError, ValueError):
            continue
        access = str(item.get("access", item.get("access_type", item.get("permission", "RO")))).upper()
        read_only = bool(item.get("read_only", item.get("readonly", False)))
        writable = access in {"RW", "R/W", "READ_WRITE", "READ-WRITE"} and not read_only
        limits = item.get("range", item.get("valid_range", {}))
        if not isinstance(limits, dict):
            limits = {}
        minimum = item.get("min", item.get("minimum", limits.get("min")))
        maximum = item.get("max", item.get("maximum", limits.get("max")))
        normalized.append({
            "address": address,
            "name": str(item.get("name", item.get("label", f"Register {address}"))),
            "access": "RW" if writable else "RO",
            "minimum": minimum,
            "maximum": maximum,
            "description": str(item.get("description", item.get("desc", ""))),
        })
    return sorted(normalized, key=lambda register: register["address"])


def create_backend() -> Any:
    """Load a user-provided adapter factory; never guesses backend APIs."""
    target = os.getenv("VFD_BACKEND_ADAPTER", "").strip()
    if not target:
        raise BackendUnavailable(
            "Backend adapter is not configured. Set VFD_BACKEND_ADAPTER to a local module and factory."
        )
    module_name, separator, factory_name = target.partition(":")
    if not separator or not module_name or not factory_name:
        raise BackendUnavailable("Use VFD_BACKEND_ADAPTER=module_name:create_adapter.")
    try:
        module = importlib.import_module(module_name)
        factory = getattr(module, factory_name)
        backend = factory()
    except Exception as exc:
        raise BackendUnavailable(f"Could not initialize the configured adapter: {exc}") from exc
    return backend


def require_method(backend: Any, method_name: str):
    """Return one explicitly implemented adapter method or explain the gap."""
    method = getattr(backend, method_name, None)
    if not callable(method):
        raise BackendUnavailable(
            f"The configured adapter does not provide {method_name}(). "
            "Connect this action to the existing project function before using it."
        )
    return method
