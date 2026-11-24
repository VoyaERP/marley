function clear_dental_case_fields(frm, fields) {
    const changes = {};

    for (const field of fields) {
        if (frm.doc[field]) {
            changes[field] = null;
        }
    }

    if (Object.keys(changes).length) {
        return frm.set_value(changes);
    }
}

frappe.ui.form.on("Dental Lab Case", {
    setup(frm) {
        // Reuse Marley Healthcare's active-patient convention.
        frm.set_query("patient", () => ({
            filters: { status: "Active" }
        }));

        frm.set_query("patient_appointment", () => ({
            filters: {
                patient: frm.doc.patient || "",
                company: frm.doc.company || ""
            }
        }));

        frm.set_query("patient_encounter", () => ({
            filters: {
                patient: frm.doc.patient || "",
                company: frm.doc.company || ""
            }
        }));

        // Link existing clinical documents; do not create them.
        for (const field of [
            "service_request", "lab_test", "diagnostic_report"
        ]) {
            frm.set_query(field, () => ({
                filters: {
                    patient: frm.doc.patient || "",
                    company: frm.doc.company || "",
                    docstatus: ["!=", 2]
                }
            }));
        }

        // Reuse ERPNext warehouse and commercial master data.
        frm.set_query("warehouse", () => ({
            filters: {
                company: frm.doc.company || "",
                is_group: 0
            }
        }));

        frm.set_query("sales_order", () => ({
            filters: {
                company: frm.doc.company || "",
                customer: frm.doc.customer || "",
                docstatus: ["!=", 2]
            }
        }));

        frm.set_query("item_code", "items", () => ({
            filters: { disabled: 0 }
        }));
    },

    case_origin(frm) {
        if (frm.doc.case_origin === "External Clinic") {
            return clear_dental_case_fields(frm, [
                "patient",
                "patient_appointment",
                "patient_encounter",
                "service_request",
                "lab_test",
                "diagnostic_report",
                "origin_branch"
            ]);
        }

        if (frm.doc.case_origin === "Internal Clinic") {
            return clear_dental_case_fields(frm, [
                "customer",
                "external_reference",
                "sales_order"
            ]);
        }
    },

    patient(frm) {
        return clear_dental_case_fields(frm, [
            "patient_appointment",
            "patient_encounter",
            "service_request",
            "lab_test",
            "diagnostic_report"
        ]);
    },

    customer(frm) {
        return clear_dental_case_fields(frm, ["sales_order"]);
    },

    company(frm) {
        return clear_dental_case_fields(frm, [
            "warehouse",
            "sales_order",
            "patient_appointment",
            "patient_encounter",
            "service_request",
            "lab_test",
            "diagnostic_report"
        ]);
    }
});
