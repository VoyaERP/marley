"""Idempotent synthetic Dental Lab Cases; no Patients, invoices or stock moves."""
import os
import frappe
from frappe.utils import add_days, nowdate

PREFIX = "DENTAL-DEMO-"


def seed(apply=False):
    assert frappe.session.user == "Administrator", (
        "Run using bench execute as Administrator"
    )

    companies = frappe.get_all("Company", pluck="name")

    company = (
        os.environ.get("DENTAL_DEMO_COMPANY")
        or frappe.defaults.get_global_default("company")
    )

    if not company and len(companies) == 1:
        company = companies[0]

    assert company in companies, (
        "Set DENTAL_DEMO_COMPANY to an existing Company"
    )

    group = os.environ.get("DENTAL_DEMO_ITEM_GROUP") or "Services"
    uom = os.environ.get("DENTAL_DEMO_UOM") or "Nos"

    cg = (
        os.environ.get("DENTAL_DEMO_CUSTOMER_GROUP")
        or frappe.db.get_single_value(
            "Selling Settings", "customer_group"
        )
    )

    tr = (
        os.environ.get("DENTAL_DEMO_TERRITORY")
        or frappe.db.get_single_value(
            "Selling Settings", "territory"
        )
    )

    for dt, value in [
        ("Item Group", group),
        ("UOM", uom),
        ("Customer Group", cg),
        ("Territory", tr),
    ]:
        assert value and frappe.db.exists(dt, value), (
            f"Configure an existing {dt} for demo: {value!r}"
        )

    assert not frappe.db.get_value(
        "Item Group", group, "is_group"
    ), "Item Group must be a leaf"

    branches = [
        "[DEMO] Dental Lab Central",
        "[DEMO] Dental Lab North",
    ]

    clinics = [
        "[DEMO] Bright Smile Clinic",
        "[DEMO] Atlas Dental Studio",
    ]

    items = [
        ("DENTAL-DEMO-CROWN", "[DEMO] Zirconia Crown"),
        ("DENTAL-DEMO-BRIDGE", "[DEMO] Ceramic Bridge"),
        ("DENTAL-DEMO-DENTURE", "[DEMO] Removable Denture"),
    ]

    examples = [
        ("001",0,0,0,"Received","Normal",-2,4),
        ("002",0,1,1,"In Production","Normal",-5,3),
        ("003",1,0,0,"Quality Check","Normal",-7,2),
        ("004",1,1,2,"Ready for Delivery","Normal",-9,1),
        ("005",0,0,1,"Delivered","Normal",-16,-3),
        ("006",1,1,0,"In Production","Urgent",-3,1),
        ("007",0,0,1,"Quality Check","Urgent",-12,-2),
        ("008",1,1,2,"Cancelled","Normal",-4,8),
        ("009",0,1,2,"Received","Urgent",-1,3),
        ("010",1,0,0,"Ready for Delivery","Normal",-7,0),
    ]

    print("Using:", company, group, uom, cg, tr)

    for branch in branches:
        if frappe.db.exists("Branch", branch):
            assert frappe.db.get_value(
                "Branch", branch, "branch"
            ) == branch

    for code, label in items:
        if frappe.db.exists("Item", code):
            assert frappe.db.get_value(
                "Item", code, "item_name"
            ) == label
            assert not frappe.db.get_value(
                "Item", code, "is_stock_item"
            )

    for clinic in clinics:
        assert len(frappe.get_all(
            "Customer",
            filters={"customer_name": clinic},
            pluck="name",
        )) <= 1

    for code, *_ in examples:
        ref = PREFIX + code

        existing = frappe.get_all(
            "Dental Lab Case",
            filters={"external_reference": ref},
            fields=["name", "company", "case_origin", "notes"],
        )

        assert len(existing) <= 1 and (
            not existing or (
                existing[0].company == company
                and existing[0].case_origin == "External Clinic"
                and (existing[0].notes or "").startswith(
                    "[" + ref + "]"
                )
            )
        ), f"Demo reference collision: {ref}"

    if not apply:
        print(
            "DRY RUN: 2 clinics, 2 branches, "
            "3 service Items, 10 cases; no changes made."
        )
        return

    for branch in branches:
        if not frappe.db.exists("Branch", branch):
            frappe.get_doc({
                "doctype": "Branch",
                "branch": branch,
            }).insert()

    for code, label in items:
        if not frappe.db.exists("Item", code):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": code,
                "item_name": label,
                "item_group": group,
                "stock_uom": uom,
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
            }).insert()

    customer_ids = []

    for clinic in clinics:
        found = frappe.get_all(
            "Customer",
            filters={"customer_name": clinic},
            pluck="name",
        )

        if found:
            customer_ids.append(found[0])
        else:
            doc = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": clinic,
                "customer_type": "Company",
                "customer_group": cg,
                "territory": tr,
            }).insert()

            customer_ids.append(doc.name)

    steps = {
        "Received": [],
        "In Production": ["In Production"],
        "Quality Check": ["In Production", "Quality Check"],
        "Ready for Delivery": [
            "In Production", "Quality Check",
            "Ready for Delivery"
        ],
        "Delivered": [
            "In Production", "Quality Check",
            "Ready for Delivery", "Delivered"
        ],
        "Cancelled": ["Cancelled"],
    }

    created = skipped = 0

    for code, ci, bi, ii, status, priority, received, due in examples:
        ref = PREFIX + code

        if frappe.db.exists(
            "Dental Lab Case",
            {"external_reference": ref},
        ):
            skipped += 1
            continue

        doc = frappe.get_doc({
            "doctype": "Dental Lab Case",
            "case_origin": "External Clinic",
            "status": "Received",
            "priority": priority,
            "company": company,
            "production_branch": branches[bi],
            "customer": customer_ids[ci],
            "external_reference": ref,
            "received_on": add_days(nowdate(), received),
            "due_date": add_days(nowdate(), due),
            "notes": (
                f"[{ref}] Fictitious dental lab demo; "
                "not actual patient work."
            ),
            "items": [{
                "item_code": items[ii][0],
                "tooth_number": "11" if ii != 2 else "Full Arch",
                "shade": "A2" if ii != 2 else "N/A",
                "qty": 1,
                "uom": uom,
                "specification": "Demo use only",
            }],
        }).insert()

        path = steps[status]

        if code == "007":
            path = [
                "In Production", "Quality Check",
                "In Production", "Quality Check"
            ]

        for next_status in path:
            doc.status = next_status
            doc.save()

        created += 1
        print("CREATED", doc.name, status)

    frappe.db.commit()

    print(
        "DEMO COMPLETE: created", created,
        "skipped", skipped
    )
