# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

import frappe
import json

@frappe.whitelist()
def sync_lead_owner_from_assignment(lead_name):
	"""
	Sync Lead Owner with Assigned To field.
	This method can be called from client-side when assignment changes.
	"""
	try:
		if not lead_name:
			return {"success": False, "message": "Lead name is required"}
		
		# Get the lead document
		lead = frappe.get_doc("Lead", lead_name)
		
		# Get assigned user from _assign field
		assigned_user = None
		
		# Check _assign field from database (most reliable)
		assign_value = frappe.db.get_value("Lead", lead_name, "_assign")
		if assign_value:
			try:
				assigned_users = json.loads(assign_value) if isinstance(assign_value, str) else assign_value
				if assigned_users and len(assigned_users) > 0:
					assigned_user = assigned_users[0]
			except:
				pass
		
		# Determine what lead_owner should be
		target_lead_owner = None
		if assigned_user:
			# Verify the user exists
			if frappe.db.exists("User", assigned_user):
				target_lead_owner = assigned_user
			else:
				target_lead_owner = "Administrator"
		else:
			target_lead_owner = "Administrator"
		
		# Update lead_owner if it's different
		current_owner = frappe.db.get_value("Lead", lead_name, "lead_owner")
		if current_owner != target_lead_owner:
			frappe.db.set_value("Lead", lead_name, "lead_owner", target_lead_owner)
			frappe.db.commit()
			# Return the new owner so client can update the field
			return {
				"success": True, 
				"message": f"Lead Owner updated to {target_lead_owner}",
				"new_owner": target_lead_owner
			}
		else:
			return {
				"success": True, 
				"message": "Lead Owner already correct",
				"new_owner": target_lead_owner
			}
		
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Error syncing Lead Owner from assignment"
		)
		return {"success": False, "message": str(e)}

def sync_lead_owner_with_assigned_to(doc, method=None):
	"""
	Sync Lead Owner with Assigned To field.
	If a lead is assigned to someone (via assignment rules or manual assignment),
	that person should also become the Lead Owner.
	If no one is assigned, keep it as Administrator.
	
	This function handles:
	- Automatic assignment via Assignment Rules (on create/update)
	- Manual assignment (when user assigns lead manually)
	- Assignment removal (when assignment is removed)
	"""
	try:
		# Skip if this is being called from within a save operation to avoid recursion
		if hasattr(frappe.local, 'sync_lead_owner_in_progress'):
			return
		
		frappe.local.sync_lead_owner_in_progress = True
		
		# Reload the document to get the latest _assign value from database
		# This is important for manual assignments where _assign might be updated
		# in the database but not yet in the document object
		doc.reload()
		
		# Get assigned user from _assign field (Frappe's standard assignment field)
		# _assign is stored as JSON string in the database
		assigned_user = None
		
		# Method 1: Check _assign field from document (after reload)
		if hasattr(doc, '_assign') and doc._assign:
			try:
				assigned_users = json.loads(doc._assign) if isinstance(doc._assign, str) else doc._assign
				if assigned_users and len(assigned_users) > 0:
					assigned_user = assigned_users[0]  # Get the first assigned user
			except:
				pass
		
		# Method 2: Check directly from database _assign field (most reliable for manual assignments)
		if not assigned_user:
			assign_value = frappe.db.get_value("Lead", doc.name, "_assign")
			if assign_value:
				try:
					assigned_users = json.loads(assign_value) if isinstance(assign_value, str) else assign_value
					if assigned_users and len(assigned_users) > 0:
						assigned_user = assigned_users[0]
				except:
					pass
		
		# Method 3: Check assigned_to field if it exists (some custom implementations use this)
		if not assigned_user and hasattr(doc, 'assigned_to') and doc.assigned_to:
			assigned_user = doc.assigned_to
		
		# Determine what lead_owner should be
		target_lead_owner = None
		if assigned_user:
			# Verify the user exists
			if frappe.db.exists("User", assigned_user):
				target_lead_owner = assigned_user
			else:
				# If assigned user doesn't exist, set to Administrator
				target_lead_owner = "Administrator"
		else:
			# If no one is assigned, set to Administrator
			target_lead_owner = "Administrator"
		
		# Update lead_owner if it's different
		# Use db.set_value to update without triggering another save cycle or hooks
		if doc.lead_owner != target_lead_owner:
			# Always use db.set_value to update (works for both new and existing documents)
			# This ensures the change is saved and doesn't trigger recursive hooks
			frappe.db.set_value("Lead", doc.name, "lead_owner", target_lead_owner)
			# Update the document object so it reflects the change
			doc.lead_owner = target_lead_owner
		
		# Clean up the flag
		delattr(frappe.local, 'sync_lead_owner_in_progress')
		
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Error syncing Lead Owner with Assigned To"
		)
		# Clean up the flag in case of error
		if hasattr(frappe.local, 'sync_lead_owner_in_progress'):
			delattr(frappe.local, 'sync_lead_owner_in_progress')

