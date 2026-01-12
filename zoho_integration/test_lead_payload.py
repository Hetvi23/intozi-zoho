"""
Test script to manually create a Lead from Zoho payload
Usage: bench --site <site> console, then: exec(open('/home/frappe/frappe-bench/apps/zoho_integration/zoho_integration/test_lead_payload.py').read())
"""

import frappe
import json

def test_create_lead():
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
			"lead_owner_name": getattr(lead, 'lead_owner_name', None)
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

# Run the test
if __name__ == "__main__" or "exec" in str(type(__file__)):
	result = test_create_lead()
	print("\nResult:", result)
