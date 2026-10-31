# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""Bo kiem thu unittest - khong can thu vien ben ngoai."""
import unittest
from datetime import timezone

from lab_w08.coordinator import DeviceMonitoringCoordinator
from lab_w08.devices import AirConditionerRemote, ProjectorRemote, TeachingDevice, WirelessMicrophone
from lab_w08.enums import AlertSeverity, DeviceStatus
from lab_w08.events import DeviceAlertEventArgs
from lab_w08.exceptions import InvalidDeviceReadingException
from lab_w08.subscribers import (
    ConsoleNotificationService, DeviceAuditLogger, FilteredAlertSubscriber,
    MaintenanceService,
)


class TestTeachingDevice(unittest.TestCase):
    def test_default_status(self):
        projector = ProjectorRemote("P1", "May chieu")
        self.assertEqual(projector.status, DeviceStatus.AVAILABLE)
        self.assertIn("100%", projector.describe_health())
        self.assertIn("phản hồi", AirConditionerRemote("A1", "AC", "R1").describe_health())
        self.assertIn("tín hiệu", WirelessMicrophone("M1", "Mic").describe_health())

    def test_status_event_contains_old_new_and_current_state(self):
        dev = ProjectorRemote("P1", "May chieu")
        records = []
        dev.status_changed.subscribe(lambda sender, event: records.append((sender.status, event)))
        dev.change_status(DeviceStatus.BORROWED)
        self.assertEqual(len(records), 1)
        current, event = records[0]
        self.assertEqual(current, DeviceStatus.BORROWED)
        self.assertEqual(event.old_status, DeviceStatus.AVAILABLE)
        self.assertEqual(event.new_status, DeviceStatus.BORROWED)
        self.assertEqual(event.device_id, "P1")
        self.assertEqual(event.changed_at.tzinfo, timezone.utc)

    def test_repeated_status_no_event(self):
        dev = ProjectorRemote("P1", "May chieu")
        received = []
        dev.status_changed.subscribe(lambda *_: received.append(1))
        dev.change_status(DeviceStatus.AVAILABLE)
        dev.change_status(DeviceStatus.BORROWED)
        dev.change_status(DeviceStatus.BORROWED)
        self.assertEqual(received, [1])

    def test_status_has_no_public_setter_and_event_no_emit(self):
        dev = ProjectorRemote("P1", "May chieu")
        with self.assertRaises(TypeError):
            TeachingDevice("D1", "Base")  # Lop co so khong duoc khoi tao.
        with self.assertRaises(AttributeError):
            dev.status = DeviceStatus.BORROWED
        self.assertFalse(hasattr(dev.status_changed, "publish"))
        self.assertFalse(hasattr(dev.alert_raised, "emit"))

    def test_invalid_status_rejected(self):
        dev = ProjectorRemote("P1", "May chieu")
        with self.assertRaises(TypeError):
            dev.change_status("Borrowed")
        self.assertEqual(dev.status, DeviceStatus.AVAILABLE)

    def test_invalid_device_id_rejected(self):
        with self.assertRaises(ValueError):
            ProjectorRemote(" ", "May chieu")


class TestProjector(unittest.TestCase):
    def test_warning_and_critical_transitions(self):
        dev = ProjectorRemote("P1", "May chieu")
        severity = []
        dev.alert_raised.subscribe(lambda _, e: severity.append(e.severity))
        for level in [80, 21, 19, 18, 5, 0, 0]:
            dev.update_battery_level(level)
        self.assertEqual(severity, [AlertSeverity.WARNING, AlertSeverity.CRITICAL])

    def test_recovery_does_not_create_warning(self):
        dev = ProjectorRemote("P1", "May chieu", battery_level=0)
        severity = []
        dev.alert_raised.subscribe(lambda _, e: severity.append(e.severity))
        dev.update_battery_level(10)
        dev.update_battery_level(100)
        self.assertEqual(severity, [])

    def test_invalid_battery_state_unchanged(self):
        dev = ProjectorRemote("P1", "May chieu")
        for invalid in [-1, 101, True]:
            with self.subTest(value=invalid):
                with self.assertRaises(InvalidDeviceReadingException) as cm:
                    dev.update_battery_level(invalid)
                self.assertEqual(cm.exception.device_id, "P1")
                self.assertEqual(dev.battery_level, 100)


class TestAirConditioner(unittest.TestCase):
    def test_unresponsive_only_on_transition(self):
        dev = AirConditionerRemote("A1", "Dieu hoa", "TC-312")
        events = []
        dev.alert_raised.subscribe(lambda _, e: events.append(e.severity))
        for value in [False, False, True, True, False]:
            dev.update_response_state(value)
        self.assertEqual(events, [AlertSeverity.CRITICAL, AlertSeverity.CRITICAL])
        self.assertFalse(dev.is_responsive)

    def test_invalid_response_type(self):
        dev = AirConditionerRemote("A1", "Dieu hoa", "TC-312")
        with self.assertRaises(TypeError):
            dev.update_response_state(0)
        self.assertTrue(dev.is_responsive)


class TestMicrophone(unittest.TestCase):
    def test_micro_battery_threshold(self):
        dev = WirelessMicrophone("M1", "Micro")
        events = []
        dev.alert_raised.subscribe(lambda _, e: events.append(e.severity))
        for value in [30, 29, 20, 0]:
            dev.update_battery_level(value)
        self.assertEqual(events, [AlertSeverity.WARNING, AlertSeverity.CRITICAL])

    def test_micro_signal_threshold(self):
        dev = WirelessMicrophone("M1", "Micro")
        events = []
        dev.alert_raised.subscribe(lambda _, e: events.append(e.severity))
        for value in [40, 39, 30, 0]:
            dev.update_signal_quality(value)
        self.assertEqual(events, [AlertSeverity.WARNING, AlertSeverity.CRITICAL])

    def test_invalid_signal_is_unchanged(self):
        dev = WirelessMicrophone("M1", "Micro")
        with self.assertRaises(InvalidDeviceReadingException) as cm:
            dev.update_signal_quality(110)
        self.assertEqual(cm.exception.invalid_value, 110)
        self.assertEqual(dev.signal_quality, 100)


class TestSubscribers(unittest.TestCase):
    def test_multiple_subscribers_for_one_alert(self):
        dev = ProjectorRemote("P1", "May chieu")
        first, second = [], []
        dev.alert_raised.subscribe(lambda _, e: first.append(e.severity))
        dev.alert_raised.subscribe(lambda _, e: second.append(e.severity))
        dev.update_battery_level(0)
        self.assertEqual(first, [AlertSeverity.CRITICAL])
        self.assertEqual(second, first)

    def test_maintenance_only_critical(self):
        dev = ProjectorRemote("P1", "May chieu")
        service = MaintenanceService()
        dev.alert_raised.subscribe(service.handle_critical_alert)
        dev.update_battery_level(19)
        self.assertEqual(len(service.requests), 0)
        dev.update_battery_level(0)
        self.assertEqual(len(service.requests), 1)

    def test_filtered_alert_callback(self):
        dev = ProjectorRemote("P1", "May chieu")
        recorded = []
        subscriber = FilteredAlertSubscriber(
            lambda e: e.severity == AlertSeverity.CRITICAL,
            lambda e: recorded.append(e.device_id),
        )
        dev.alert_raised.subscribe(subscriber.handle_alert)
        dev.update_battery_level(19)
        dev.update_battery_level(0)
        self.assertEqual(recorded, ["P1"])

    def test_readonly_service_history(self):
        logger = DeviceAuditLogger()
        maintenance = MaintenanceService()
        self.assertIsInstance(logger.entries, tuple)
        self.assertIsInstance(maintenance.requests, tuple)
        with self.assertRaises(AttributeError):
            maintenance.requests.append("fake")

    def test_faulty_handler_does_not_block_other_handlers(self):
        dev = ProjectorRemote("P1", "May chieu")
        seen = []
        def faulty(sender, e):
            raise RuntimeError("Subscriber error")
        dev.alert_raised.subscribe(faulty)
        dev.alert_raised.subscribe(lambda _, e: seen.append(e.severity))
        dev.update_battery_level(0)
        self.assertEqual(seen, [AlertSeverity.CRITICAL])
        self.assertEqual(len(dev.delivery_errors), 1)
        self.assertEqual(dev.delivery_errors[0].error_type, "RuntimeError")

    def test_subscribe_unsubscribe_idempotent(self):
        dev = ProjectorRemote("P1", "May chieu")
        events = []
        def handler(_, e):
            events.append(e)
        dev.alert_raised.subscribe(handler)
        dev.alert_raised.subscribe(handler)
        self.assertEqual(dev.alert_raised.handler_count, 1)
        dev.update_battery_level(19)
        dev.alert_raised.unsubscribe(handler)
        dev.alert_raised.unsubscribe(handler)
        dev.update_battery_level(0)
        self.assertEqual(len(events), 1)

    def test_handler_unsubscribes_during_emit(self):
        dev = ProjectorRemote("P1", "May chieu")
        records = []
        def first(sender, e):
            records.append("first")
            dev.alert_raised.unsubscribe(second)
        def second(sender, e):
            records.append("second")
        dev.alert_raised.subscribe(first)
        dev.alert_raised.subscribe(second)
        dev.update_battery_level(19)
        self.assertEqual(records, ["first", "second"])
        dev.update_battery_level(0)
        self.assertEqual(records, ["first", "second", "first"])


class TestCoordinator(unittest.TestCase):
    def setUp(self):
        self.projector = ProjectorRemote("P1", "May chieu")
        self.notifications = []
        self.notifier = ConsoleNotificationService(self.notifications.append)
        self.logger = DeviceAuditLogger()
        self.maintenance = MaintenanceService()
        self.coordinator = DeviceMonitoringCoordinator(
            [self.projector, self.projector],
            self.notifier, self.logger, self.maintenance,
        )

    def test_register_twice_does_not_duplicate_notifications(self):
        self.coordinator.subscribe()
        self.coordinator.subscribe()
        self.projector.update_battery_level(0)
        self.assertEqual(len(self.notifications), 1)
        self.assertEqual(len(self.maintenance.requests), 1)
        self.assertEqual(self.projector.alert_raised.handler_count, 2)

    def test_status_logger(self):
        self.coordinator.subscribe()
        self.projector.change_status(DeviceStatus.BORROWED)
        self.assertEqual(len(self.logger.entries), 1)
        self.assertIn("Available -> Borrowed", self.logger.entries[0])

    def test_unsubscribe_and_dispose(self):
        self.coordinator.subscribe()
        self.coordinator.unsubscribe()
        self.coordinator.unsubscribe()
        self.projector.update_battery_level(19)
        self.assertEqual(len(self.notifications), 0)
        self.coordinator.dispose()
        self.assertEqual(self.projector.alert_raised.handler_count, 0)
        with self.assertRaises(RuntimeError):
            self.coordinator.subscribe()

    def test_context_manager_auto_dispose(self):
        with DeviceMonitoringCoordinator(
            [self.projector], self.notifier, self.logger, self.maintenance
        ):
            self.projector.update_battery_level(19)
        self.projector.update_battery_level(0)
        self.assertEqual(len(self.notifications), 1)
        self.assertEqual(len(self.maintenance.requests), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
