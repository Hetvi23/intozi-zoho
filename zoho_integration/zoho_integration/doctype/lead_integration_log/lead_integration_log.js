// Copyright (c) 2025, jignesh@nesscale.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead Integration Log", {
    refresh(frm) {
        if (frm.doc.status === "Failed") {
            frm.add_custom_button("Retry", function() {
                frappe.call({
                    method: "zoho_integration.zoho_api.process_webhook_lead",
                    args: { log_name: frm.doc.name },
                    callback: () => frm.reload_doc()
                });
            });
        }
    }
});