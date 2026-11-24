frappe.query_reports["Radiology Reception"] = {
  filters: [
    {
      fieldname: "appointment_date",
      label: __("Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
      reqd: 1
    },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company")
    },
    {
      fieldname: "service_unit",
      label: __("Imaging Room"),
      fieldtype: "Link",
      options: "Healthcare Service Unit"
    },
    {
      fieldname: "status",
      label: __("Status"),
      fieldtype: "Select",
      options: "\\nScheduled\\nOpen\\nConfirmed\\nChecked In\\nChecked Out\\nClosed\\nNo Show\\nCancelled"
    }
  ],

  onload(report) {
    const changeStatus = (target) => {
      const dialog = new frappe.ui.Dialog({
        title: __(target),
        fields: [{
          fieldname: "appointment",
          fieldtype: "Link",
          label: __("Appointment"),
          options: "Patient Appointment",
          reqd: 1,
          get_query: () => ({
            filters: {
              appointment_date: frappe.query_report.get_filter_value(
                "appointment_date"
              )
            }
          })
        }],
        primary_action_label: __(target),
        primary_action(values) {
          frappe.call({
            method: "healthcare.healthcare.api.radiology_reception.transition",
            type: "POST",
            args: {
              appointment: values.appointment,
              target: target
            },
            callback(response) {
              if (response.exc) return;
              dialog.hide();
              frappe.show_alert({
                message: __("Updated") + ": " + response.message.status,
                indicator: "green"
              });
              report.refresh();
            }
          });
        }
      });
      dialog.show();
    };

    report.page.add_inner_button(
      __("Check In"), () => changeStatus("Checked In")
    );
    report.page.add_inner_button(
      __("Check Out"), () => changeStatus("Checked Out")
    );
    report.page.add_inner_button(
      __("Calendar"),
      () => frappe.set_route("List", "Patient Appointment", "Calendar")
    );
    report.page.add_inner_button(
      __("Book Appointment"),
      () => frappe.set_route("List", "Patient Appointment", "List")
    );
  }
};
