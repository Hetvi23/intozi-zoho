# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

import frappe
import json

def sync_lead_owner_with_assigned_to(doc, method=None):
	"""
	Sync Lead Owner with Assigned To field.
	If a lead is assigned to someone through round robin logic,
	that person should also become the Lead Owner.
	If no one is assigned, keep it as Administrator.
	"""
	try:
		# Skip if this is being called from within a save operation to avoid recursion
		if hasattr(frappe.local, 'sync_lead_owner_in_progress'):
			return
		
		frappe.local.sync_lead_owner_in_progress = True
		
		# Get assigned user from _assign field (Frappe's standard assignment field)
		assigned_user = None
		if hasattr(doc, '_assign') and doc._assign:
			try:
				assigned_users = json.loads(doc._assign) if isinstance(doc._assign, str) else doc._assign
				if assigned_users and len(assigned_users) > 0:
					assigned_user = assigned_users[0]  # Get the first assigned user
			except:
				pass
		
		# Also check assigned_to field if it exists (some custom implementations use this)
		if not assigned_user and hasattr(doc, 'assigned_to') and doc.assigned_to:
			assigned_user = doc.assigned_to
		
		# Set lead_owner based on assignment
		if assigned_user:
			# Verify the user exists
			if frappe.db.exists("User", assigned_user):
				# Set lead_owner to the assigned user
				if doc.lead_owner != assigned_user:
					doc.lead_owner = assigned_user
			else:
				# If assigned user doesn't exist, set to Administrator
				if doc.lead_owner != "Administrator":
					doc.lead_owner = "Administrator"
		else:
			# If no one is assigned, set to Administrator
			if not doc.lead_owner or doc.lead_owner != "Administrator":
				doc.lead_owner = "Administrator"
		
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

