import tempfile
import unittest
from pathlib import Path

from bot import db


class EmployeeFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.init_db(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        db._conn.close()
        self.tmp.cleanup()

    def test_registration_to_active(self):
        db.start_registration(1, "aigerim_s")
        self.assertEqual(db.get_employee(1)["status"], "awaiting_name")

        db.submit_name(1, "Айгерим Сапарова")
        employee = db.get_employee(1)
        self.assertEqual(employee["status"], "pending")
        self.assertEqual(employee["full_name"], "Айгерим Сапарова")

        self.assertTrue(db.change_employee_status(1, "pending", "active"))
        self.assertEqual([e["telegram_id"] for e in db.list_employees("active")], [1])

    def test_double_click_approve_only_once(self):
        db.start_registration(1, None)
        db.submit_name(1, "Ержан Ахметов")
        self.assertTrue(db.change_employee_status(1, "pending", "active"))
        self.assertFalse(db.change_employee_status(1, "pending", "active"))

    def test_reject_after_approve_is_ignored(self):
        db.start_registration(1, None)
        db.submit_name(1, "Ержан Ахметов")
        db.change_employee_status(1, "pending", "active")
        self.assertFalse(db.change_employee_status(1, "pending", "rejected"))
        self.assertEqual(db.get_employee(1)["status"], "active")

    def test_name_ignored_unless_awaiting(self):
        db.start_registration(1, None)
        db.submit_name(1, "Марат Ким")
        db.change_employee_status(1, "pending", "active")
        db.submit_name(1, "Другое имя")
        self.assertEqual(db.get_employee(1)["full_name"], "Марат Ким")

    def test_removed_employee_can_register_again(self):
        db.start_registration(1, None)
        db.submit_name(1, "Марат Ким")
        db.change_employee_status(1, "pending", "active")
        db.change_employee_status(1, "active", "removed")
        db.start_registration(1, "marat")
        self.assertEqual(db.get_employee(1)["status"], "awaiting_name")


class GroupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.init_db(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        db._conn.close()
        self.tmp.cleanup()

    def test_pending_group_approved_once(self):
        db.save_group(-100, "Отдел продаж", "pending")
        self.assertTrue(db.change_group_status(-100, "pending", "active"))
        self.assertFalse(db.change_group_status(-100, "pending", "rejected"))
        self.assertEqual([g["title"] for g in db.list_groups("active")], ["Отдел продаж"])


if __name__ == "__main__":
    unittest.main()
