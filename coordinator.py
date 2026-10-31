# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""Noi dang ky / huy dang ky event tap trung, tuong duong IDisposable."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Callable

from .devices import TeachingDevice
from .events import DeviceAlertEventArgs
from .subscribers import (
    ConsoleNotificationService, DeviceAuditLogger, MaintenanceService,
)


class DeviceMonitoringCoordinator:
    def __init__(
        self, devices: Iterable[TeachingDevice],
        notification_service: ConsoleNotificationService,
        audit_logger: DeviceAuditLogger,
        maintenance_service: MaintenanceService,
        extra_alert_handlers: Iterable[Callable[[object, DeviceAlertEventArgs], None]] = (),
    ):
        # Khoanh danh sach / loai lap doi tuong de khong phu thuoc collection dau vao.
        self._devices = tuple(dict.fromkeys(devices))
        if not all(isinstance(d, TeachingDevice) for d in self._devices):
            raise TypeError("Chi chap nhan cac TeachingDevice")
        self._notification = notification_service
        self._audit = audit_logger
        self._maintenance = maintenance_service
        self._extra_handlers = tuple(extra_alert_handlers)
        self._subscribed = False
        self._disposed = False

    def subscribe(self) -> None:
        if self._disposed:
            raise RuntimeError("Coordinator da duoc dispose")
        if self._subscribed:
            return
        for device in self._devices:
            device.status_changed.subscribe(self._audit.handle_status_changed)
            device.alert_raised.subscribe(self._notification.handle_alert)
            device.alert_raised.subscribe(self._maintenance.handle_critical_alert)
            for handler in self._extra_handlers:
                device.alert_raised.subscribe(handler)
        self._subscribed = True

    def unsubscribe(self) -> None:
        if not self._subscribed:
            return
        for device in self._devices:
            device.status_changed.unsubscribe(self._audit.handle_status_changed)
            device.alert_raised.unsubscribe(self._notification.handle_alert)
            device.alert_raised.unsubscribe(self._maintenance.handle_critical_alert)
            for handler in self._extra_handlers:
                device.alert_raised.unsubscribe(handler)
        self._subscribed = False

    def dispose(self) -> None:
        self.unsubscribe()
        self._disposed = True

    def __enter__(self):
        self.subscribe()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.dispose()
