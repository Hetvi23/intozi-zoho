# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	"""
	Add custom fields to Lead doctype for Zoho integration.
	This patch adds custom fields that come from Zoho CRM (Y column in the mapping spreadsheet).
	"""
	custom_fields = {
		"Lead": [
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
	}
	
	create_custom_fields(custom_fields, ignore_validate=True, update=True)
	frappe.clear_cache()

