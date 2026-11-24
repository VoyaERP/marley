frappe.query_reports["Dental Lab Operations"] = {
    filters: [
        {fieldname:"company", label:__("Company"), fieldtype:"Link", options:"Company", default:frappe.defaults.get_user_default("Company")},
        {fieldname:"production_branch", label:__("Production Branch"), fieldtype:"Link", options:"Branch"},
        {fieldname:"case_origin", label:__("Case Origin"), fieldtype:"Select", options:"\\nInternal Clinic\\nExternal Clinic"},
        {fieldname:"customer", label:__("Clinic"), fieldtype:"Link", options:"Customer"},
        {fieldname:"status", label:__("Status"), fieldtype:"Select", options:"\\nReceived\\nIn Production\\nQuality Check\\nReady for Delivery\\nDelivered\\nCancelled"},
        {fieldname:"priority", label:__("Priority"), fieldtype:"Select", options:"\\nNormal\\nUrgent"},
        {fieldname:"from_date", label:__("From Date"), fieldtype:"Date"},
        {fieldname:"to_date", label:__("To Date"), fieldtype:"Date"},
        {fieldname:"overdue_only", label:__("Overdue Only"), fieldtype:"Check"},
        {fieldname:"demo_only", label:__("Demo Only"), fieldtype:"Check"}
    ]
};
