import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

ALLOWED_TRANSITIONS = {
    "Received": {"In Production", "Cancelled"},
    "In Production": {"Quality Check", "Cancelled"},
    "Quality Check": {
        "In Production", "Ready for Delivery", "Cancelled"
    },
    "Ready for Delivery": {
        "Quality Check", "Delivered", "Cancelled"
    },
    "Delivered": set(),
    "Cancelled": set(),
}

def validate_status_transition(previous, current):
    if current not in ALLOWED_TRANSITIONS:
        frappe.throw(
            _("Invalid dental case status: {0}").format(current)
        )
    if previous is None:
        if current != "Received":
            frappe.throw(
                _("New cases must start in Received status")
            )
        return
    if previous in ("Delivered", "Cancelled"):
        frappe.throw(
            _("Delivered/Cancelled cases cannot be edited")
        )
    if current != previous and current not in ALLOWED_TRANSITIONS.get(
        previous, set()
    ):
        frappe.throw(
            _("Invalid status change: {0} to {1}").format(
                previous, current
            )
        )

def validate_case_context(origin, customer, patient):
    if origin not in ("Internal Clinic", "External Clinic"):
        frappe.throw(_("Select a valid case origin"))
    if origin == "External Clinic" and not customer:
        frappe.throw(
            _("Customer is mandatory for external clinic cases")
        )
    if origin == "Internal Clinic" and not patient:
        frappe.throw(
            _("Patient is mandatory for internal clinic cases")
        )

def validate_case_items(items):
    if not items:
        frappe.throw(_("Add at least one dental work item"))
    for index, row in enumerate(items, 1):
        if not row.get("item_code"):
            frappe.throw(
                _("Missing Item in row {0}").format(index)
            )
        if flt(row.get("qty")) <= 0:
            frappe.throw(
                _("Quantity must exceed zero in row {0}").format(index)
            )

class DentalLabCase(Document):
    def validate(self):
        validate_case_context(
            self.case_origin, self.customer, self.patient
        )
        validate_case_items(self.get("items"))

        if (
            self.received_on
            and self.due_date
            and getdate(self.due_date) < getdate(self.received_on)
        ):
            frappe.throw(
                _("Delivery date cannot precede received date")
            )

        for dt, field in (
            ("Patient Appointment", "patient_appointment"),
            ("Patient Encounter", "patient_encounter"),
        ):
            ref = self.get(field)
            if ref:
                linked_patient = frappe.db.get_value(
                    dt, ref, "patient"
                )
                if not linked_patient or (
                    self.patient and self.patient != linked_patient
                ):
                    frappe.throw(
                        _("Patient mismatch in {0}").format(dt)
                    )

        if self.sales_order:
            so = frappe.db.get_value(
                "Sales Order",
                self.sales_order,
                ["company", "customer", "docstatus"],
                as_dict=True,
            )
            if (
                not so
                or so.docstatus == 2
                or so.company != self.company
                or so.customer != self.customer
            ):
                frappe.throw(
                    _("Sales Order customer/company mismatch or order cancelled")
                )

        self.validate_clinical_links()

        previous = self.get_doc_before_save()

        validate_status_transition(
            previous.status if previous else None,
            self.status,
        )

        if previous and (
            previous.status != "Received"
            or self.status != "Received"
        ):
            for field in (
                "company",
                "production_branch",
                "case_origin",
                "customer",
                "patient",
            ):
                if self.get(field) != previous.get(field):
                    frappe.throw(
                        _("Cannot change {0} after production starts").format(
                            field
                        )
                    )

    def validate_clinical_links(self):
        """Validate existing clinical references without creating records."""
        links = (
            ("service_request", "Service Request"),
            ("lab_test", "Lab Test"),
            ("diagnostic_report", "Diagnostic Report"),
        )

        if self.case_origin != "Internal Clinic":
            if any(self.get(field) for field, _ in links):
                frappe.throw(
                    _("Clinical links are restricted to internal-clinic cases")
                )
            return

        for field, doctype in links:
            name = self.get(field)
            if not name:
                continue

            clinical = frappe.db.get_value(
                doctype,
                name,
                ["patient", "company", "docstatus"],
                as_dict=True,
            )

            if (
                not clinical
                or not self.patient
                or clinical.patient != self.patient
                or clinical.company != self.company
                or clinical.docstatus == 2
            ):
                frappe.throw(
                    _("{0} must belong to the same patient and company "
                      "and must not be cancelled").format(doctype)
                )
