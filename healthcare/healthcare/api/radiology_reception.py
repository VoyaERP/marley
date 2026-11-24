"""Reception actions on the existing Patient Appointment."""
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def _authorized():
    allowed = {"Healthcare Administrator", "System Manager"}
    if frappe.session.user != "Administrator" and not (
        allowed & set(frappe.get_roles())
    ):
        frappe.throw(_("Reception access required"), frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def transition(appointment, target):
    _authorized()

    if target not in ("Checked In", "Checked Out"):
        frappe.throw(_("Invalid reception action"))

    doc = frappe.get_doc("Patient Appointment", appointment)
    doc.check_permission("write")

    if not doc.service_unit:
        frappe.throw(_("Select a Healthcare Service Unit first"))

    if not frappe.db.get_value(
        "Healthcare Service Unit", doc.service_unit, "allow_appointments"
    ):
        frappe.throw(_("Service unit does not allow appointments"))

    # Serialize check-ins for the same imaging room.
    locked_unit = doc.service_unit
    frappe.db.sql(
        "select name from `tabHealthcare Service Unit` "
        "where name=%s for update",
        (locked_unit,),
    )
    doc.reload()
    doc.check_permission("write")

    if doc.service_unit != locked_unit:
        frappe.throw(_("Service unit changed while processing check-in"))

    if target == "Checked In":
        if doc.status == "Checked In":
            return {
                "appointment": doc.name,
                "position": doc.position_in_queue,
                "status": doc.status,
            }

        if doc.status not in ("Scheduled", "Open", "Confirmed", "No Show"):
            frappe.throw(_("Appointment cannot be checked in"))

        if getdate(doc.appointment_date) != getdate(nowdate()):
            frappe.throw(_("Check-in requires today's appointment"))

        patient = frappe.db.get_value(
            "Patient", doc.patient, ["status", "customer"], as_dict=True
        )

        if not patient or patient.status != "Active":
            frappe.throw(_("The linked Patient must be active"))

        if not patient.customer or not frappe.db.exists(
            "Customer", patient.customer
        ):
            frappe.throw(
                _("Link the Patient to an ERPNext Customer before check-in")
            )

    else:
        if doc.status == "Checked Out":
            return {
                "appointment": doc.name,
                "position": doc.position_in_queue,
                "status": doc.status,
            }

        if doc.status != "Checked In":
            frappe.throw(_("Check-out requires Checked In status"))

    doc.status = target
    doc.save()

    return {
        "appointment": doc.name,
        "position": doc.position_in_queue,
        "status": doc.status,
    }
