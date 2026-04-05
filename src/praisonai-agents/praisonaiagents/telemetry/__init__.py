"""
PraisonAI Agents Telemetry Module - DISABLED for security.

All telemetry and performance monitoring is permanently disabled.
No data is collected or sent to any external service.
"""

from .telemetry import (
    MinimalTelemetry,
    TelemetryCollector,
    get_telemetry,
    enable_telemetry,
    disable_telemetry,
    force_shutdown_telemetry,
)
from .integration import (
    enable_performance_mode,
    disable_performance_mode,
    cleanup_telemetry_resources,
)

# Performance monitoring stubs
PERFORMANCE_MONITORING_AVAILABLE = False

__all__ = [
    'get_telemetry',
    'enable_telemetry',
    'disable_telemetry',
    'force_shutdown_telemetry',
    'MinimalTelemetry',
    'TelemetryCollector',
    'enable_performance_mode',
    'disable_performance_mode',
    'cleanup_telemetry_resources',
    'PERFORMANCE_MONITORING_AVAILABLE',
]
