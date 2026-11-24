"""Reception queue using existing Healthcare appointments."""
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
    roles = set(frappe.get_roles())

    if frappe.session.user != "Administrator" and not (
        roles & {"Healthcare Administrator", "System Manager"}
    ):
        frappe.throw(_("Reception access required"), frappe.PermissionError)

    f = frappe._dict(filters or {})

    conditions = {
        "appointment_date": str(
            getdate(f.get("appointment_date") or nowdate())
        ),
        "docstatus": ["<", 2],
    }

    for field in ("company", "service_unit", "status"):
        if f.get(field):
            conditions[field] = f[field]

    fields = [
        "name", "patient", "patient_name", "appointment_type",
        "appointment_date", "appointment_time", "service_unit",
        "company", "practitioner", "status", "position_in_queue",
    ]

    rows = frappe.get_list(
        "Patient Appointment",
        fields=fields,
        filters=conditions,
        limit_page_length=500,
        order_by="appointment_time asc, creation asc",
    )

    patient_ids = sorted({row.patient for row in rows if row.patient})
    customer_map = {}

    if patient_ids:
        customer_map = {
            p.name: p.customer
            for p in frappe.get_all(
                "Patient",
                filters={"name": ["in", patient_ids]},
                fields=["name", "customer"],
                limit_page_length=500,
            )
        }

    for row in rows:
        row.customer = customer_map.get(row.patient) or ""
        row.customer_linked = _("Yes") if row.customer else _("Missing")

    rows.sort(
        key=lambda row: (
            0 if row.status == "Checked In" else 1,
            row.position_in_queue or 999999,
            str(row.appointment_time or ""),
            row.name,
        )
    )

    definitions = [
        ("name", "Appointment", "Link", 160, "Patient Appointment"),
        ("position_in_queue", "Queue", "Int", 70, None),
        ("status", "Status", "Data", 110, None),
        ("patient", "Patient", "Link", 130, "Patient"),
        ("patient_name", "Patient Name", "Data", 160, None),
        ("customer", "ERP Customer", "Link", 150, "Customer"),
        ("customer_linked", "Customer Linked", "Data", 125, None),
        ("appointment_type", "Exam Type", "Link", 125, "Appointment Type"),
        ("service_unit", "Imaging Room", "Link", 140, "Healthcare Service Unit"),
        ("appointment_date", "Date", "Date", 100, None),
        ("appointment_time", "Time", "Time", 90, None),
        ("practitioner", "Practitioner", "Link", 140, "Healthcare Practitioner"),
    ]

    columns = []

    for field, label, kind, width, target in definitions:
        column = {
            "fieldname": field,
            "label": _(label),
            "fieldtype": kind,
            "width": width,
        }
        if target:
            column["options"] = target
        columns.append(column)

    return columns, rows
