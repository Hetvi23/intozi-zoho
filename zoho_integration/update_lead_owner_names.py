# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

"""
Script to update lead_owner_name based on lead_owner field.
This can be run from System Console or via bench execute.

Usage in System Console: Copy the script content (without imports)
Usage via bench: bench --site [site-name] execute zoho_integration.update_lead_owner_names.update_lead_owner_names
"""

import frappe

@frappe.whitelist()
def update_lead_owner_names():
	"""
	Update lead_owner_name field for all leads based on their lead_owner field.
	"""
	try:
		# Check if lead_owner_name field exists
		lead_meta = frappe.get_meta("Lead")
		if not lead_meta.has_field("lead_owner_name"):
			return {
				"success": False,
				"message": "lead_owner_name field does not exist on Lead doctype"
			}
		
		# Get all leads with lead_owner set (including those where owner_name might be wrong)
		# Specifically target leads where owner is set but name is "Administrator" or empty
		leads = frappe.get_all("Lead", 
			fields=["name", "lead_owner", "lead_owner_name"],
			filters=[
				["lead_owner", "!=", ""],
				["lead_owner", "!=", None]
			]
		)
		
		updated_count = 0
		skipped_count = 0
		error_count = 0
		
		if hasattr(frappe.local, 'form_dict'):
			frappe.msgprint(f"Processing {len(leads)} leads...", alert=True)
		else:
			print(f"Processing {len(leads)} leads...")
		
		for lead in leads:
			try:
				lead_name = lead.name
				lead_owner = lead.lead_owner
				current_owner_name = lead.lead_owner_name or ""
				
				# Skip if no lead_owner
				if not lead_owner:
					skipped_count = skipped_count + 1
					continue
				
				# Get the owner's full name
				owner_name = "Administrator"
				if lead_owner != "Administrator":
					if frappe.db.exists("User", lead_owner):
						try:
							user_doc = frappe.get_doc("User", lead_owner)
							owner_name = user_doc.full_name or user_doc.name
						except Exception as e:
							owner_name = lead_owner  # Fallback to username if user doc fails
					else:
						owner_name = lead_owner  # Fallback to username if user doesn't exist
				
				# Update if different OR if owner is set but name is still Administrator/empty
				# This handles the case where owner is set but name wasn't updated
				should_update = False
				if current_owner_name != owner_name:
					should_update = True
				elif lead_owner != "Administrator" and (current_owner_name == "Administrator" or not current_owner_name or current_owner_name == ""):
					# Special case: owner is set but name is still Administrator or empty
					should_update = True
				
				if should_update:
					frappe.db.set_value("Lead", lead_name, "lead_owner_name", owner_name)
					updated_count = updated_count + 1
				else:
					skipped_count = skipped_count + 1
				
				# Commit every 100 records
				if (updated_count + skipped_count) % 100 == 0:
					frappe.db.commit()
					
			except Exception as e:
				error_count = error_count + 1
				frappe.log_error(
					message=f"Error updating lead {lead.name}: {str(e)}\n{frappe.get_traceback()}",
					title="Error updating lead owner name"
				)
				continue
		
		# Final commit
		frappe.db.commit()
		
		message = f"""
		Update completed!
		- Updated: {updated_count} leads
		- Skipped (already correct): {skipped_count} leads
		- Errors: {error_count} leads
		- Total processed: {len(leads)} leads
		"""
		
		if hasattr(frappe.local, 'form_dict'):
			frappe.msgprint(message, alert=True, indicator="green")
		else:
			print(message)
		
		return {
			"success": True,
			"updated": updated_count,
			"skipped": skipped_count,
			"errors": error_count,
			"total": len(leads)
		}
		
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Error updating lead owner names"
		)
		error_msg = f"Error: {str(e)}"
		if hasattr(frappe.local, 'form_dict'):
			frappe.msgprint(error_msg, alert=True, indicator="red")
		else:
			print(error_msg)
		return {"success": False, "message": str(e)}
