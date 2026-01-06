# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

import frappe

def add_zoho_custom_fields_to_lead():
	"""
	Add custom fields to Lead doctype for Zoho integration.
	This patch adds custom fields that come from Zoho CRM (Y column in the mapping spreadsheet).
	"""
	try:
		# Check if Lead doctype exists
		if not frappe.db.exists("DocType", "Lead"):
			return
		
		# Get Lead doctype
		lead_doc = frappe.get_doc("DocType", "Lead")
		
		# Add custom fields from Zoho (based on spreadsheet mapping)
		# These are the custom fields from the Y column in the mapping spreadsheet
		# Field names match the spreadsheet exactly
		custom_fields_to_add = [
			{
				"fieldname": "secondary_email",
				"fieldtype": "Data",
				"label": "Secondary Email",
				"options": "Email",
				"description": "Secondary Email from Zoho CRM"
			},
			{
				"fieldname": "tag",
				"fieldtype": "Data",
				"label": "Tag",
				"description": "Tag from Zoho CRM"
			},
			{
				"fieldname": "utm_content",
				"fieldtype": "Data",
				"label": "UTM Content",
				"description": "UTM Content from Zoho CRM"
			},
			{
				"fieldname": "utm_term",
				"fieldtype": "Data",
				"label": "UTM Term",
				"description": "UTM Term from Zoho CRM"
			},
			{
				"fieldname": "utm_source",
				"fieldtype": "Data",
				"label": "UTM Source",
				"description": "UTM Source from Zoho CRM"
			},
			{
				"fieldname": "utm_campaign",
				"fieldtype": "Data",
				"label": "UTM Campaign",
				"description": "UTM Campaign from Zoho CRM"
			},
			{
				"fieldname": "utm_medium",
				"fieldtype": "Data",
				"label": "UTM Medium",
				"description": "UTM Medium from Zoho CRM"
			},
			{
				"fieldname": "referrer_url",
				"fieldtype": "Data",
				"label": "Referrer URL",
				"description": "Referrer URL from Zoho CRM"
			},
			{
				"fieldname": "mobile_alternate",
				"fieldtype": "Data",
				"label": "Mobile Alternate",
				"description": "Mobile Alternate from Zoho CRM"
			},
			{
				"fieldname": "phone_alternate",
				"fieldtype": "Data",
				"label": "Phone Alternate",
				"description": "Phone Alternate from Zoho CRM"
			}
		]
		
		# Add custom fields if they don't exist
		fields_added = 0
		for field_data in custom_fields_to_add:
			field_exists = any(
				f.fieldname == field_data["fieldname"]
				for f in lead_doc.fields
			)
			
			if not field_exists:
				lead_doc.append("fields", field_data)
				fields_added += 1
		
		# Save the doctype only if changes were made
		if fields_added > 0:
			lead_doc.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.logger().info(f"Zoho custom fields: Added {fields_added} field(s) to Lead doctype.")
		
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Error adding Zoho custom fields to Lead doctype"
		)
		raise

