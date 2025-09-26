# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LeadFieldMapping(Document):
	pass


@frappe.whitelist()
def get_lead_fieldnames():
    meta = frappe.get_meta("Lead", cached=False)
    fieldnames = [
        f.fieldname
        for f in meta.fields
        if not f.hidden and f.fieldtype not in ["Section Break", "Column Break", "Table"]
    ]
    return fieldnames
