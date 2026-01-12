"""
Test script to manually create a Lead from Zoho payload
"""
import frappe
import json

@frappe.whitelist()
def test_create_lead_with_payload():
	"""Test creating a lead with the provided payload"""
	
	# The payload from the user
	payload = {
		"id": "921314000007778001",
		"lead_owner": "Naresh Kamboj",
		"company": "MIlestone Tech Pvt Ltd",
		"lead_name": " Ji",
		"first_name": "",
		"last_name": "Ji",
		"salutation": "",
		"title": "Ghanshyam",
		"designation": "Ghanshyam",
		"email": "test@gmail.com",
		"secondary_email": "",
		"email_opt_out": "false",
		"phone": "9818454640",
		"mobile": "",
		"fax": "",
		"website": "",
		"lead_source": "Linkedin",
		"lead_status": "",
		"industry": "",
		"annual_revenue": "",
		"skype_id": "",
		"twitter": "",
		"street": "",
		"city": "",
		"state": "",
		"zip_code": "",
		"country": "",
		"description": "",
		"created_by": "Naresh Kamboj",
		"created_time": "01-10-2026 12:12:17",
		"modified_by": "Naresh Kamboj",
		"modified_time": "01-10-2026 12:12:17",
		"tag": "",
		"Lead_Sync_Status": "",
		"rating": "",
		"no_of_employees": ""
	}
	
	try:
		# Check if Lead Field Mapping exists, create/update if not
		if frappe.db.exists("Lead Field Mapping", "Zoho to ERPNext"):
			# Delete and recreate to ensure correct mapping
			frappe.delete_doc("Lead Field Mapping", "Zoho to ERPNext", force=1, ignore_permissions=True)
			frappe.db.commit()
			print("\n⚠️ Updated existing Lead Field Mapping 'Zoho to ERPNext'...")
		else:
			print("\n⚠️ Lead Field Mapping 'Zoho to ERPNext' not found. Creating it...")
		
		mapping_doc = frappe.get_doc({
			"doctype": "Lead Field Mapping",
			"title": "Zoho to ERPNext",
			"lead_field_mapping_details": [
				{"erpnext_field": "lead_name", "external_field": "lead_name"},
				{"erpnext_field": "first_name", "external_field": "first_name"},
				{"erpnext_field": "last_name", "external_field": "last_name"},
				{"erpnext_field": "salutation", "external_field": "salutation"},
				{"erpnext_field": "company_name", "external_field": "company"},
				{"erpnext_field": "title", "external_field": "title"},
				{"erpnext_field": "designation", "external_field": "designation"},
				{"erpnext_field": "email_id", "external_field": "email"},
				{"erpnext_field": "secondary_email", "external_field": "secondary_email"},
				{"erpnext_field": "phone", "external_field": "phone"},
				{"erpnext_field": "mobile_no", "external_field": "mobile"},
				{"erpnext_field": "fax", "external_field": "fax"},
				{"erpnext_field": "website", "external_field": "website"},
				{"erpnext_field": "source", "external_field": "lead_source"},
				{"erpnext_field": "status", "external_field": "lead_status"},
				{"erpnext_field": "industry", "external_field": "industry"},
				{"erpnext_field": "annual_revenue", "external_field": "annual_revenue"},
				{"erpnext_field": "skype_id", "external_field": "skype_id"},
				{"erpnext_field": "twitter", "external_field": "twitter"},
				{"erpnext_field": "address_line1", "external_field": "street"},
				{"erpnext_field": "city", "external_field": "city"},
				{"erpnext_field": "state", "external_field": "state"},
				{"erpnext_field": "pincode", "external_field": "zip_code"},
				{"erpnext_field": "country", "external_field": "country"},
				{"erpnext_field": "description", "external_field": "description"},
				{"erpnext_field": "tag", "external_field": "tag"},
				{"erpnext_field": "no_of_employees", "external_field": "no_of_employees"},
				{"erpnext_field": "lead_owner", "external_field": "lead_owner"},
			]
		})
		mapping_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		print("✅ Lead Field Mapping created/updated successfully!\n")
		
		# Import the function
		from zoho_integration.zoho_api import upsert_zoho_lead
		
		print("=" * 80)
		print("Testing Lead Creation with Payload")
		print("=" * 80)
		print(f"\nPayload Lead Source: {payload.get('lead_source')}")
		print(f"Payload Lead Owner: {payload.get('lead_owner')}")
		print(f"Payload Email: {payload.get('email')}")
		print(f"Payload Phone: {payload.get('phone')}")
		print(f"Payload Company: {payload.get('company')}")
		
		# Call the function
		print("\n" + "-" * 80)
		print("Calling upsert_zoho_lead()...")
		print("-" * 80)
		
		lead = upsert_zoho_lead(payload)
		
		print(f"\n✅ Lead created/updated successfully!")
		print(f"Lead Name: {lead.name}")
		print(f"Lead Source (mapped): {lead.source}")
		print(f"Lead Owner: {lead.lead_owner}")
		print(f"Company: {lead.company}")
		print(f"Email: {lead.email_id}")
		print(f"Phone: {lead.phone}")
		print(f"Zoho Integration ID: {lead.custom_integration_lead_id}")
		
		# Check if assignment rule ran
		lead.reload()
		assign_value = frappe.db.get_value("Lead", lead.name, "_assign")
		print(f"\nAssignment (_assign): {assign_value}")
		
		# Reload to get latest values
		lead.reload()
		print(f"\nFinal Lead Owner: {lead.lead_owner}")
		print(f"Final Lead Owner Name: {getattr(lead, 'lead_owner_name', 'N/A')}")
		
		print("\n" + "=" * 80)
		print("Test Completed Successfully!")
		print("=" * 80)
		
		return {
			"success": True,
			"lead_name": lead.name,
			"source": lead.source,
			"lead_owner": lead.lead_owner,
			"lead_owner_name": getattr(lead, 'lead_owner_name', None),
			"assignment": assign_value
		}
		
	except Exception as e:
		error_msg = f"Error creating lead: {str(e)}\n{frappe.get_traceback()}"
		print("\n" + "=" * 80)
		print("❌ ERROR OCCURRED")
		print("=" * 80)
		print(error_msg)
		frappe.log_error(message=error_msg, title="Test Lead Creation Failed")
		return {
			"success": False,
			"error": str(e),
			"traceback": frappe.get_traceback()
		}
