# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""Chay demo thuc hanh W08 - chay bang python main.py."""
from lab_w08.coordinator import DeviceMonitoringCoordinator
from lab_w08.devices import (
    ProjectorRemote, AirConditionerRemote, WirelessMicrophone,
)
from lab_w08.enums import AlertSeverity, DeviceStatus
from lab_w08.exceptions import InvalidDeviceReadingException
from lab_w08.subscribers import (
    ConsoleNotificationService, DeviceAuditLogger, MaintenanceService,
    FilteredAlertSubscriber,
)


def main() -> None:
    projector = ProjectorRemote("PJ-01", "Dieu khien may chieu")
    aircon = AirConditionerRemote("AC-01", "Dieu khien dieu hoa", "TC-312")
    microphone = WirelessMicrophone("MIC-01", "Micro khong day")

    logger = DeviceAuditLogger()
    maintenance = MaintenanceService()
    notification = ConsoleNotificationService()

    # Callback tuong duong delegate AlertFilter trong de bai C#.
    critical_only = FilteredAlertSubscriber(
        lambda alert: alert.severity == AlertSeverity.CRITICAL,
        lambda alert: print(f"CRITICAL CALLBACK: {alert.device_id} - {alert.message}"),
    )
    coordinator = DeviceMonitoringCoordinator(
        [projector, aircon, microphone], notification, logger, maintenance,
        extra_alert_handlers=[critical_only.handle_alert],
    )
    print("=== BẮT ĐẦU THEO DÕI ===")
    coordinator.subscribe()
    coordinator.subscribe()  # Co tinh goi hai lan: khong duoc dang ky trung.
    projector.change_status(DeviceStatus.BORROWED)
    projector.change_status(DeviceStatus.BORROWED)  # Khong co them nhat ky.
    projector.update_battery_level(19)
    projector.update_battery_level(15)  # Van trong vung Warning: khong lap canh bao.
    projector.update_battery_level(0)
    aircon.update_response_state(False)
    aircon.update_response_state(False)
    microphone.update_signal_quality(39)
    microphone.update_signal_quality(0)
    microphone.update_battery_level(29)
    microphone.change_status(DeviceStatus.UNDER_MAINTENANCE)
    try:
        microphone.update_battery_level(101)
    except InvalidDeviceReadingException as error:
        print(f"ĐÃ BẮT NGOẠI LỆ: {error}")

    print(f"SỐ BẢN GHI AUDIT: {len(logger.entries)}")
    for item in logger.entries:
        print("AUDIT:", item)
    print(f"SỐ YÊU CẦU BẢO TRÌ: {len(maintenance.requests)}")
    for item in maintenance.requests:
        print("MAINTENANCE:", item)

    coordinator.dispose()
    print("=== ĐÃ HỦY ĐĂNG KÝ ===")
    projector.update_battery_level(100)
    projector.update_battery_level(0)
    print(f"SỐ YÊU CẦU BẢO TRÌ SAU DISPOSE: {len(maintenance.requests)}")


if __name__ == "__main__":
    main()
