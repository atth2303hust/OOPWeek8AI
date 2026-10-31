# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""He thong dang ky/huy dang ky va phat su kien khong phu thuoc subscriber."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Generic, TypeVar

from .enums import AlertSeverity, DeviceStatus


@dataclass(frozen=True)
class DeviceStatusChangedEventArgs:
    device_id: str
    old_status: DeviceStatus
    new_status: DeviceStatus
    changed_at: datetime


@dataclass(frozen=True)
class DeviceAlertEventArgs:
    device_id: str
    message: str
    severity: AlertSeverity
    occurred_at: datetime


@dataclass(frozen=True)
class EventDeliveryError:
    handler: str
    error_type: str
    message: str


T = TypeVar("T")
EventHandler = Callable[[object, T], None]


class EventSubscription(Generic[T]):
    """Giao dien cong khai chi cho dang ky/huy dang ky, KHONG co emit()."""
    def __init__(self, channel: _EventChannel[T]):
        self.__channel = channel

    def subscribe(self, handler: EventHandler[T]) -> None:
        self.__channel.subscribe(handler)

    def unsubscribe(self, handler: EventHandler[T]) -> None:
        self.__channel.unsubscribe(handler)

    @property
    def handler_count(self) -> int:
        return self.__channel.handler_count


class _EventChannel(Generic[T]):
    """Publisher so huu kenh su kien; ham publish chi duoc goi noi bo."""
    def __init__(self):
        self.__handlers: list[EventHandler[T]] = []
        self.__delivery_errors: list[EventDeliveryError] = []
        self.subscription = EventSubscription(self)

    @property
    def handler_count(self) -> int:
        return len(self.__handlers)

    @property
    def delivery_errors(self) -> tuple[EventDeliveryError, ...]:
        return tuple(self.__delivery_errors)

    def subscribe(self, handler: EventHandler[T]) -> None:
        if not callable(handler):
            raise TypeError("Event handler phai la mot callable")
        if handler not in self.__handlers:
            self.__handlers.append(handler)

    def unsubscribe(self, handler: EventHandler[T]) -> None:
        try:
            self.__handlers.remove(handler)
        except ValueError:
            pass  # Huy nhieu lan van an toan.

    def publish(self, sender: object, event_args: T) -> None:
        # Chup nhanh danh sach de tranh loi neu handler tu huy dang ky.
        for handler in tuple(self.__handlers):
            try:
                handler(sender, event_args)
            except Exception as exc:  # Bien chuong trinh demo khong dung khi 1 subscriber loi.
                self.__delivery_errors.append(
                    EventDeliveryError(repr(handler), type(exc).__name__, str(exc))
                )
