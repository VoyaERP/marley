import frappe
from frappe.tests.utils import FrappeTestCase
from healthcare.dental_lab.doctype.dental_lab_case.dental_lab_case import (
    validate_case_context,
    validate_case_items,
    validate_status_transition,
)

class TestDentalLabCase(FrappeTestCase):
    def test_case_status(self):
        validate_status_transition(None, "Received")
        validate_status_transition("Received", "In Production")
        with self.assertRaises(frappe.ValidationError):
            validate_status_transition("Received", "Delivered")
        with self.assertRaises(frappe.ValidationError):
            validate_status_transition("Delivered", "Delivered")

    def test_case_party(self):
        validate_case_context("External Clinic", "C-001", None)
        validate_case_context("Internal Clinic", None, "P-001")
        with self.assertRaises(frappe.ValidationError):
            validate_case_context("External Clinic", None, None)

    def test_line_validation(self):
        validate_case_items([{"item_code": "I-001", "qty": 1}])
        with self.assertRaises(frappe.ValidationError):
            validate_case_items([{"item_code": "I-001", "qty": 0}])
