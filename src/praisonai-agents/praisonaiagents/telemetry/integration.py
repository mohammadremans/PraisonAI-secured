"""
Telemetry integration module - DISABLED for security.

All instrumentation functions are no-ops.
No monkey-patching of Agent or AgentManager constructors occurs.
"""

from typing import Any, Optional, TYPE_CHECKING
from contextlib import contextmanager

if TYPE_CHECKING:
    from .telemetry import MinimalTelemetry


def instrument_agent(agent: Any, telemetry: Optional['MinimalTelemetry'] = None, performance_mode: bool = False) -> Any:
    """No-op - does not instrument agents."""
    return agent


def instrument_workflow(workflow: Any, telemetry: Optional['MinimalTelemetry'] = None, performance_mode: bool = False) -> Any:
    """No-op - does not instrument workflows."""
    return workflow


def auto_instrument_all(telemetry: Optional['MinimalTelemetry'] = None, performance_mode: bool = False) -> None:
    """No-op - auto-instrumentation is disabled."""
    pass


def enable_performance_mode() -> None:
    """No-op."""
    pass


def disable_performance_mode() -> None:
    """No-op."""
    pass


def cleanup_telemetry_resources() -> None:
    """No-op - no resources to clean up."""
    pass
