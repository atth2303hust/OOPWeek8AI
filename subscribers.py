# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""Cac thanh phan nhan su kien va delegate filter."""
from __future__ import annotations

from typing import Callable, TypeAlias

from .enums import AlertSeverity
from .events import DeviceAlertEventArgs, DeviceStatusChangedEventArgs

AlertFilter: TypeAlias = Callable[[DeviceAlertEventArgs], bool]
AlertAction: TypeAlias = Callable[[DeviceAlertEventArgs], None]


class ConsoleNotificationService:
    def __init__(self, output: Callable[[str], None] = print):
        self._output = output

    def handle_alert(self, sender: object, e: DeviceAlertEventArgs) -> None:
        self._output(f"[{e.severity.name}] {e.device_id}: {e.message}")


class DeviceAuditLogger:
    def __init__(self):
        self._entries: list[str] = []

    @property
    def entries(self) -> tuple[str, ...]:
        return tuple(self._entries)  # Snapshot bat bien.

    def handle_status_changed(
        self, sender: object, e: DeviceStatusChangedEventArgs
    ) -> None:
        self._entries.append(
            f"{e.changed_at.isoformat()}: {e.device_id}, "
            f"{e.old_status.value} -> {e.new_status.value}"
        )


class MaintenanceService:
    def __init__(self):
        self._requests: list[str] = []

    @property
    def requests(self) -> tuple[str, ...]:
        return tuple(self._requests)

    def handle_critical_alert(self, sender: object, e: DeviceAlertEventArgs) -> None:
        if e.severity == AlertSeverity.CRITICAL:
            self._requests.append(
                f"Maintenance request for {e.device_id}: {e.message}"
            )


class FilteredAlertSubscriber:
    """Giong delegate: truyen filter va action vao constructor."""
    def __init__(self, alert_filter: AlertFilter, action: AlertAction):
        if not callable(alert_filter) or not callable(action):
            raise TypeError("filter/action phai la callable")
        self._filter = alert_filter
        self._action = action

    def handle_alert(self, sender: object, e: DeviceAlertEventArgs) -> None:
        if self._filter(e):
            self._action(e)
