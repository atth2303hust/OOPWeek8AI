# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""Cac danh muc trang thai va muc do canh bao."""
from enum import Enum, IntEnum


class DeviceStatus(Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    UNDER_MAINTENANCE = "UnderMaintenance"


class AlertSeverity(IntEnum):
    INFORMATION = 1
    WARNING = 2
    CRITICAL = 3
