# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""Publisher va ba loai thiet bi phong hoc."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from .enums import AlertSeverity, DeviceStatus
from .events import (
    DeviceAlertEventArgs, DeviceStatusChangedEventArgs,
    EventDeliveryError, EventSubscription, _EventChannel,
)
from .exceptions import InvalidDeviceReadingException


def _check_reading(device_id: str, value: int) -> None:
    # bool la lop con cua int trong Python: can loai tru True/False.
    if type(value) is not int or not 0 <= value <= 100:
        raise InvalidDeviceReadingException(device_id, value)


class TeachingDevice(ABC):
    """Lop co so: thiet bi khong biet ai dang nghe su kien."""
    def __init__(self, device_id: str, name: str):
        if not isinstance(device_id, str) or not device_id.strip():
            raise ValueError("Ma thiet bi khong duoc rong")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Ten thiet bi khong duoc rong")
        self._id = device_id
        self._name = name
        self._status = DeviceStatus.AVAILABLE
        self.__status_channel = _EventChannel[DeviceStatusChangedEventArgs]()
        self.__alert_channel = _EventChannel[DeviceAlertEventArgs]()

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> DeviceStatus:
        return self._status

    @property
    def status_changed(self) -> EventSubscription[DeviceStatusChangedEventArgs]:
        return self.__status_channel.subscription

    @property
    def alert_raised(self) -> EventSubscription[DeviceAlertEventArgs]:
        return self.__alert_channel.subscription

    @property
    def delivery_errors(self) -> tuple[EventDeliveryError, ...]:
        return (
            self.__status_channel.delivery_errors
            + self.__alert_channel.delivery_errors
        )

    @abstractmethod
    def describe_health(self) -> str:
        """Mỗi lớp thiết bị phải ghi đè mô tả tình trạng riêng."""
        raise NotImplementedError

    def change_status(self, new_status: DeviceStatus) -> None:
        if not isinstance(new_status, DeviceStatus):
            raise TypeError("new_status phai la DeviceStatus")
        if new_status == self._status:
            return  # Khong tao su kien trang thai trung lap.
        old = self._status
        self._status = new_status  # Cap nhat TRUOC khi phat su kien.
        self._on_status_changed(
            DeviceStatusChangedEventArgs(
                self.id, old, new_status, datetime.now(timezone.utc)
            )
        )

    def _raise_alert(self, message: str, severity: AlertSeverity) -> None:
        self._on_alert_raised(
            DeviceAlertEventArgs(
                self.id, message, severity, datetime.now(timezone.utc)
            )
        )

    def _on_status_changed(self, event: DeviceStatusChangedEventArgs) -> None:
        self.__status_channel.publish(self, event)

    def _on_alert_raised(self, event: DeviceAlertEventArgs) -> None:
        self.__alert_channel.publish(self, event)


def _battery_band(level: int, threshold: int) -> int:
    if level == 0:
        return 2  # Critical.
    return 1 if level < threshold else 0  # Warning hoac an toan.


class ProjectorRemote(TeachingDevice):
    def __init__(self, device_id: str, name: str, battery_level: int = 100):
        super().__init__(device_id, name)
        _check_reading(device_id, battery_level)
        self._battery_level = battery_level

    @property
    def battery_level(self) -> int:
        return self._battery_level

    def describe_health(self) -> str:
        return f"Pin máy chiếu: {self._battery_level}%"

    def update_battery_level(self, new_level: int) -> None:
        _check_reading(self.id, new_level)
        old_band = _battery_band(self._battery_level, 20)
        new_band = _battery_band(new_level, 20)
        self._battery_level = new_level
        # Chi canh bao khi xau di va buoc vao vung canh bao nghiem trong hon.
        if new_band > old_band:
            severity = (AlertSeverity.CRITICAL if new_band == 2
                        else AlertSeverity.WARNING)
            self._raise_alert(f"Pin máy chiếu còn {new_level}%", severity)


class AirConditionerRemote(TeachingDevice):
    def __init__(self, device_id: str, name: str, assigned_room: str):
        super().__init__(device_id, name)
        if not assigned_room.strip():
            raise ValueError("Phong duoc gan khong duoc rong")
        self._assigned_room = assigned_room
        self._is_responsive = True

    @property
    def assigned_room(self) -> str:
        return self._assigned_room

    @property
    def is_responsive(self) -> bool:
        return self._is_responsive

    def describe_health(self) -> str:
        return f"Điều hòa {self._assigned_room}: phản hồi={self._is_responsive}"

    def update_response_state(self, is_responsive: bool) -> None:
        if type(is_responsive) is not bool:
            raise TypeError("is_responsive phai la bool")
        was_responsive = self._is_responsive
        self._is_responsive = is_responsive
        if was_responsive and not is_responsive:
            self._raise_alert(
                f"Điều hòa tại phòng {self.assigned_room} không phản hồi",
                AlertSeverity.CRITICAL,
            )


class WirelessMicrophone(TeachingDevice):
    def __init__(
        self, device_id: str, name: str,
        battery_level: int = 100, signal_quality: int = 100,
    ):
        super().__init__(device_id, name)
        _check_reading(device_id, battery_level)
        _check_reading(device_id, signal_quality)
        self._battery_level = battery_level
        self._signal_quality = signal_quality

    @property
    def battery_level(self) -> int:
        return self._battery_level

    @property
    def signal_quality(self) -> int:
        return self._signal_quality

    def describe_health(self) -> str:
        return (f"Micro: pin={self._battery_level}%, "
                f"tín hiệu={self._signal_quality}%")

    def update_battery_level(self, new_level: int) -> None:
        _check_reading(self.id, new_level)
        old_band = _battery_band(self._battery_level, 30)
        new_band = _battery_band(new_level, 30)
        self._battery_level = new_level
        if new_band > old_band:
            severity = (AlertSeverity.CRITICAL if new_band == 2
                        else AlertSeverity.WARNING)
            self._raise_alert(f"Pin micro còn {new_level}%", severity)

    def update_signal_quality(self, new_quality: int) -> None:
        _check_reading(self.id, new_quality)
        old_band = _battery_band(self._signal_quality, 40)
        new_band = _battery_band(new_quality, 40)
        self._signal_quality = new_quality
        if new_band > old_band:
            severity = (AlertSeverity.CRITICAL if new_band == 2
                        else AlertSeverity.WARNING)
            self._raise_alert(f"Tín hiệu micro còn {new_quality}%", severity)
