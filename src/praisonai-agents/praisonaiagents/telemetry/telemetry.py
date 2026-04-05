"""
Telemetry module - DISABLED for security.

All telemetry functions are no-ops. PostHog has been removed as a dependency.
No data is collected or sent anywhere.
"""

import threading
from typing import Any, Dict, Optional


def _is_monitoring_disabled() -> bool:
    """Always returns True - monitoring is permanently disabled."""
    return True


class MinimalTelemetry:
    """No-op telemetry stub. All methods are silent no-ops."""

    def __init__(self, enabled: bool = None) -> None:
        self.enabled = False
        self.session_id = None
        self._metrics: Dict[str, Any] = {}
        self._shutdown_complete = True

    def track_agent_execution(self, agent_name: str = None, success: bool = True, async_mode: bool = False) -> None:
        pass

    def track_task_completion(self, task_name: str = None, success: bool = True) -> None:
        pass

    def track_tool_usage(self, tool_name: str = "", success: bool = True, execution_time: float = None) -> None:
        pass

    def track_error(self, error_type: str = None) -> None:
        pass

    def track_feature_usage(self, feature_name: str = "") -> None:
        pass

    def get_metrics(self) -> Dict[str, Any]:
        return {"enabled": False}

    def flush(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


# Global telemetry instance
_telemetry_instance: Optional[MinimalTelemetry] = None
_telemetry_instance_lock = threading.Lock()


def get_telemetry() -> MinimalTelemetry:
    """Get the global telemetry instance (always disabled)."""
    global _telemetry_instance
    with _telemetry_instance_lock:
        if _telemetry_instance is None:
            _telemetry_instance = MinimalTelemetry()
        return _telemetry_instance


def disable_telemetry() -> None:
    """No-op - telemetry is already permanently disabled."""
    pass


def force_shutdown_telemetry() -> None:
    """No-op - nothing to shut down."""
    pass


def enable_telemetry() -> None:
    """No-op - telemetry cannot be re-enabled."""
    pass


# Backward compatibility
class TelemetryCollector:
    """Backward compatibility wrapper - all methods are no-ops."""

    def __init__(self, backend: str = "minimal", service_name: str = "praisonai-agents", **kwargs) -> None:
        self.telemetry = get_telemetry()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def trace_agent_execution(self, agent_name: str, **attributes):
        from contextlib import contextmanager

        @contextmanager
        def _trace():
            yield None
        return _trace()

    def trace_task_execution(self, task_name: str, agent_name: str = None, **attributes):
        from contextlib import contextmanager

        @contextmanager
        def _trace():
            yield None
        return _trace()

    def trace_tool_call(self, tool_name: str, **attributes):
        from contextlib import contextmanager

        @contextmanager
        def _trace():
            yield None
        return _trace()

    def trace_llm_call(self, model: str = None, **attributes):
        from contextlib import contextmanager

        @contextmanager
        def _trace():
            yield None
        return _trace()

    def record_tokens(self, prompt_tokens: int, completion_tokens: int, model: str = None) -> None:
        pass

    def record_cost(self, cost: float, model: str = None) -> None:
        pass

    def get_metrics(self) -> Dict[str, Any]:
        return {"enabled": False}
