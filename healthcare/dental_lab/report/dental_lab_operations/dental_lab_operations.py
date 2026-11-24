import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate


def execute(filters=None):
    f = frappe._dict(filters or {})
    where = []

    for field in (
        "company", "production_branch", "case_origin",
        "customer", "status", "priority"
    ):
        if f.get(field):
            where.append(
                ["Dental Lab Case", field, "=", f[field]]
            )

    if (
        f.get("from_date") and f.get("to_date")
        and getdate(f.from_date) > getdate(f.to_date)
    ):
        frappe.throw(_("From Date must not exceed To Date"))

    if f.get("from_date"):
        where.append([
            "Dental Lab Case", "received_on", ">=", f.from_date
        ])

    if f.get("to_date"):
        where.append([
            "Dental Lab Case", "received_on", "<=", f.to_date
        ])

    if cint(f.get("overdue_only")):
        where.extend([
            [
                "Dental Lab Case", "due_date",
                "<", nowdate()
            ],
            [
                "Dental Lab Case", "status",
                "not in", ["Delivered", "Cancelled"]
            ],
        ])

    if cint(f.get("demo_only")):
        where.append([
            "Dental Lab Case", "external_reference",
            "like", "DENTAL-DEMO-%"
        ])

    definitions = [
        ("name", "Case", "Link", 160, "Dental Lab Case"),
        ("status", "Status", "Data", 150, None),
        ("priority", "Priority", "Data", 90, None),
        ("company", "Company", "Link", 150, "Company"),
        ("production_branch", "Production Branch", "Link", 160, "Branch"),
        ("case_origin", "Origin", "Data", 120, None),
        ("customer", "Clinic", "Link", 160, "Customer"),
        ("patient", "Patient", "Link", 130, "Patient"),
        ("received_on", "Received", "Date", 105, None),
        ("due_date", "Due", "Date", 105, None),
        ("overdue_days", "Overdue Days", "Int", 100, None),
        ("service_request", "Service Request", "Link", 150, "Service Request"),
        ("lab_test", "Lab Test", "Link", 140, "Lab Test"),
        ("diagnostic_report", "Diagnostic Report", "Link", 160, "Diagnostic Report"),
        ("external_reference", "External Reference", "Data", 165, None),
    ]

    columns = []

    for field, label, kind, width, link in definitions:
        col = {
            "fieldname": field,
            "label": _(label),
            "fieldtype": kind,
            "width": width,
        }
        if link:
            col["options"] = link
        columns.append(col)

    rows = frappe.get_list(
        "Dental Lab Case",
        fields=[
            col["fieldname"] for col in columns
            if col["fieldname"] != "overdue_days"
        ],
        filters=where,
        order_by="due_date asc, modified desc",
        limit_page_length=5000,
    )

    today = getdate(nowdate())
    summary = {}

    for row in rows:
        row["overdue_days"] = (
            max(0, (today - getdate(row.due_date)).days)
            if row.due_date
            and row.status not in ("Delivered", "Cancelled")
            else 0
        )

        summary[row.status] = summary.get(row.status, 0) + 1

    chart = (
        {
            "data": {
                "labels": list(summary),
                "datasets": [{
                    "name": _("Cases"),
                    "values": list(summary.values()),
                }],
            },
            "type": "bar",
        }
        if summary else None
    )

    return columns, rows, None, chart
