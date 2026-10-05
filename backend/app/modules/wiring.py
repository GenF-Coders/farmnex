"""The one place that mounts optional components (Crop Rescue, forecaster, routes, voice tools).

Each component is switched on by an environment flag (default off) and has its own host file,
`app/modules/<host_module>.py`, with `mount(app)` and optionally `start()` / `stop()`.
Later sessions create their host file; they never edit this file or `app/main.py`.

A broken or missing component must never stop the backend: hosts are imported inside
`mount_components` (not at the top of the file), and any failure is logged once and skipped.
"""

import importlib
import logging
import os
from types import ModuleType

from fastapi import FastAPI

logger = logging.getLogger(__name__)

COMPONENTS = [
    # (flag env var,            host module under app.modules)
    ("ENABLE_CROP_RESCUE", "crop_rescue_host"),
    ("ENABLE_FORECAST", "forecast_host"),
    ("ENABLE_ROUTE_OPTIMIZER", "routes_host"),
    ("ENABLE_VOICE_TOOLS", "voice_tools_host"),
]

# Hosts whose mount() worked; start/stop only touch these.
_mounted: list[ModuleType] = []


def _flag_is_on(flag: str) -> bool:
    return os.getenv(flag, "false").strip().lower() == "true"


def mount_components(app: FastAPI) -> None:
    """Mount every component whose flag is "true". Failures are logged and skipped."""
    _mounted.clear()

    for flag, host_name in COMPONENTS:
        if not _flag_is_on(flag):
            continue

        try:
            host = importlib.import_module(f"app.modules.{host_name}")
            host.mount(app)
        except Exception:
            logger.exception(
                "Component %s is NOT mounted: could not load or mount app.modules.%s. "
                "Fix the error above or set %s=false.",
                flag,
                host_name,
                flag,
            )
            continue

        _mounted.append(host)
        logger.info("Component mounted: %s (%s)", flag, host_name)


def start_components() -> None:
    """Call start() on mounted hosts that have it (e.g. start a scheduler)."""
    _call_on_mounted("start")


def stop_components() -> None:
    """Call stop() on mounted hosts that have it, in reverse order."""
    _call_on_mounted("stop", reverse=True)


def _call_on_mounted(method_name: str, reverse: bool = False) -> None:
    for host in reversed(_mounted) if reverse else list(_mounted):
        method = getattr(host, method_name, None)
        if not callable(method):
            continue

        try:
            method()
        except Exception:
            logger.exception("Component %s() failed in %s; continuing.", method_name, host.__name__)
