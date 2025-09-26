// Copyright (c) 2025, jignesh@nesscale.com and contributors
// For license information, please see license.txt

async function set_lead_field_options(frm) {
    if (!frm._lead_field_options) {
        let res = await frappe.call({
            method: "zoho_integration.zoho_integration.doctype.lead_field_mapping.lead_field_mapping.get_lead_fieldnames"
        });
        frm._lead_field_options = res.message || [];
    }

    let options = frm._lead_field_options.join("\n");

    frm.fields_dict["lead_field_mapping_details"].grid.update_docfield_property(
        "erpnext_field",
        "options",
        options
    );
    frm.fields_dict["lead_field_mapping_details"].grid.refresh();
}

frappe.ui.form.on("Lead Field Mapping", {
    onload: async function(frm) {
        await set_lead_field_options(frm);
    },
    refresh: async function(frm) {
        await set_lead_field_options(frm);
    }
});

frappe.ui.form.on("Lead Field Mapping Details", {
    form_render: function(frm, cdt, cdn) {
        if (frm._lead_field_options) {
            let options = frm._lead_field_options.join("\n");
            frm.fields_dict["lead_field_mapping_details"].grid.update_docfield_property(
                "erpnext_field",
                "options",
                options
            );
        }
    }
});
