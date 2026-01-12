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
		
		# Get lead_owner_name (full name of the owner)
		lead_owner_name = None
		if target_lead_owner and target_lead_owner != "Administrator":
			user_doc = frappe.get_doc("User", target_lead_owner)
			lead_owner_name = user_doc.full_name or user_doc.name
		else:
			lead_owner_name = "Administrator"
		
		# Update lead_owner and lead_owner_name if different
		current_owner = frappe.db.get_value("Lead", lead_name, "lead_owner")
		update_fields = {}
		
		if current_owner != target_lead_owner:
			update_fields["lead_owner"] = target_lead_owner
		
		# Check if lead_owner_name field exists and update it
		lead_meta = frappe.get_meta("Lead")
		if lead_meta.has_field("lead_owner_name"):
			current_owner_name = frappe.db.get_value("Lead", lead_name, "lead_owner_name")
			if current_owner_name != lead_owner_name:
				update_fields["lead_owner_name"] = lead_owner_name
		
		if update_fields:
			frappe.db.set_value("Lead", lead_name, update_fields)
			frappe.db.commit()
			# Return the new owner so client can update the field
			return {
				"success": True, 
				"message": f"Lead Owner updated to {target_lead_owner}",
				"new_owner": target_lead_owner,
				"new_owner_name": lead_owner_name
			}
		else:
			return {
				"success": True, 
				"message": "Lead Owner already correct",
				"new_owner": target_lead_owner,
				"new_owner_name": lead_owner_name
			}
		
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Error syncing Lead Owner from assignment"
		)
		return {"success": False, "message": str(e)}

def sync_lead_owner_name_from_owner(doc, method=None):
	"""
	Sync lead_owner_name when lead_owner is manually changed.
	This is called on validate to ensure lead_owner_name is updated when user manually changes lead_owner.
	"""
	try:
		# Skip if this is being called from within a save operation to avoid recursion
		if hasattr(frappe.local, 'sync_lead_owner_name_in_progress'):
			return
		
		frappe.local.sync_lead_owner_name_in_progress = True
		
		# Only proceed if lead_owner_name field exists
		lead_meta = frappe.get_meta("Lead")
		if not lead_meta.has_field("lead_owner_name"):
			delattr(frappe.local, 'sync_lead_owner_name_in_progress')
			return
		
		# Get current lead_owner from document
		lead_owner = getattr(doc, "lead_owner", None)
		if not lead_owner:
			lead_owner = "Administrator"
		
		# Get the owner's full name
		owner_name = "Administrator"
		if lead_owner != "Administrator":
			if frappe.db.exists("User", lead_owner):
				try:
					user_doc = frappe.get_doc("User", lead_owner)
					owner_name = user_doc.full_name or user_doc.name
				except:
					owner_name = lead_owner  # Fallback to username
			else:
				owner_name = lead_owner  # Fallback to username
		
		# Update lead_owner_name in the document
		current_owner_name = getattr(doc, "lead_owner_name", None) or ""
		if current_owner_name != owner_name:
			doc.lead_owner_name = owner_name
		
		# Clean up the flag
		delattr(frappe.local, 'sync_lead_owner_name_in_progress')
		
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Error syncing Lead Owner Name"
		)
		# Clean up the flag in case of error
		if hasattr(frappe.local, 'sync_lead_owner_name_in_progress'):
			delattr(frappe.local, 'sync_lead_owner_name_in_progress')


def sync_lead_owner_with_assigned_to(doc, method=None):
	"""
	Sync Lead Owner with Assigned To field (for auto-assignment).
	If a lead is assigned via assignment rules, that person becomes the Lead Owner.
	If no one is assigned, set to Administrator.
	
	However, if lead_owner was manually changed and differs from assignment,
	respect the manual change and don't override it.
	
	This function handles:
	- Automatic assignment via Assignment Rules (on create/update)
	- Manual assignment (when user assigns lead manually)
	- Assignment removal (when assignment is removed)
	"""
	try:
		# Skip if change_lead_owner checkbox is ticked (manual mode enabled)
		if hasattr(doc, 'change_lead_owner') and doc.change_lead_owner:
			return
		
		# Skip if this is being called from within a save operation to avoid recursion
		if hasattr(frappe.local, 'sync_lead_owner_in_progress'):
			return
		
		frappe.local.sync_lead_owner_in_progress = True
		
		# Get lead_owner from document (this reflects any manual changes the user made)
		doc_lead_owner = getattr(doc, "lead_owner", None) or "Administrator"
		
		# Get current lead_owner from database
		db_lead_owner = "Administrator"
		if doc.name:
			db_lead_owner = frappe.db.get_value("Lead", doc.name, "lead_owner") or "Administrator"
		else:
			# New document - no database value yet
			db_lead_owner = "Administrator"
		
		# Get assigned user from database (most reliable source)
		assigned_user = None
		if doc.name:
			assign_value = frappe.db.get_value("Lead", doc.name, "_assign")
			if assign_value:
				try:
					assigned_users = json.loads(assign_value) if isinstance(assign_value, str) else assign_value
					if assigned_users and len(assigned_users) > 0:
						assigned_user = assigned_users[0]
				except:
					pass
		
		# Also check from document if available
		if not assigned_user and hasattr(doc, '_assign') and doc._assign:
			try:
				assigned_users = json.loads(doc._assign) if isinstance(doc._assign, str) else doc._assign
				if assigned_users and len(assigned_users) > 0:
					assigned_user = assigned_users[0]
			except:
				pass
		
		# Check assigned_to field if it exists
		if not assigned_user and hasattr(doc, 'assigned_to') and doc.assigned_to:
			assigned_user = doc.assigned_to
		
		# Determine what lead_owner should be based on assignment
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
		
		# KEY LOGIC: 
		# Only update lead_owner from assignment if the database lead_owner is "Administrator" or matches assignment
		# NEVER update if database lead_owner differs from assignment AND is not "Administrator"
		# This ensures manual changes are always preserved
		
		should_update_from_assignment = False
		
		# For existing documents: Check database value (source of truth)
		if doc.name:
			# First check: If document value was manually changed in this save (differs from DB) and is not "Administrator"
			# Then it's a manual change - NEVER override
			if doc_lead_owner != db_lead_owner and doc_lead_owner != "Administrator":
				# User manually changed it in this save - don't override
				should_update_from_assignment = False
			elif db_lead_owner == target_lead_owner:
				# Already matches - sync lead_owner_name
				should_update_from_assignment = True
			elif db_lead_owner == "Administrator" and target_lead_owner != "Administrator":
				# No manual owner set in DB, assignment exists - auto-assign
				should_update_from_assignment = True
			else:
				# Database has lead_owner that differs from assignment and is not "Administrator"
				# This means it was manually set previously - NEVER override it
				should_update_from_assignment = False
		else:
			# New document: Check document value
			if doc_lead_owner == target_lead_owner:
				should_update_from_assignment = True
			elif doc_lead_owner == "Administrator" and target_lead_owner != "Administrator":
				should_update_from_assignment = True
			elif doc_lead_owner != target_lead_owner and doc_lead_owner != "Administrator":
				# Document has manual owner - don't override
				should_update_from_assignment = False
		
		# If we should update from assignment, do it
		if should_update_from_assignment:
			# Get lead_owner_name (full name of the owner)
			lead_owner_name = None
			if target_lead_owner and target_lead_owner != "Administrator":
				user_doc = frappe.get_doc("User", target_lead_owner)
				lead_owner_name = user_doc.full_name or user_doc.name
			else:
				lead_owner_name = "Administrator"
			
			# Update lead_owner and lead_owner_name
			update_fields = {}
			
			# Note: We use doc.lead_owner here (which may have been restored if manually changed)
			# But since should_update_from_assignment is True, we know it wasn't manually changed
			current_doc_owner = getattr(doc, "lead_owner", None) or "Administrator"
			if current_doc_owner != target_lead_owner:
				update_fields["lead_owner"] = target_lead_owner
				# Update the document object so it reflects the change
				doc.lead_owner = target_lead_owner
			
			# Check if lead_owner_name field exists and update it
			lead_meta = frappe.get_meta("Lead")
			if lead_meta.has_field("lead_owner_name"):
				current_owner_name = getattr(doc, "lead_owner_name", None) or ""
				if current_owner_name != lead_owner_name:
					update_fields["lead_owner_name"] = lead_owner_name
					doc.lead_owner_name = lead_owner_name
			
			if update_fields:
				# Always use db.set_value to update (works for both new and existing documents)
				# This ensures the change is saved and doesn't trigger recursive hooks
				frappe.db.set_value("Lead", doc.name, update_fields)
		else:
			# Manual change detected - just ensure lead_owner_name is synced to current lead_owner
			# This will be handled by sync_lead_owner_name_from_owner on validate
			pass
		
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


@frappe.whitelist()
def sync_all_leads_owner_from_assignment():
	"""
	Sync Lead Owner for all existing leads based on their current assignments.
	This method can be run to update all leads that don't have the correct owner.
	
	Usage:
		bench --site [site-name] execute zoho_integration.lead_utils.sync_all_leads_owner_from_assignment
	"""
	try:
		# Get all leads
		leads = frappe.get_all("Lead", fields=["name", "lead_owner", "_assign"])
		
		updated_count = 0
		skipped_count = 0
		error_count = 0
		
		# Use print for console compatibility, msgprint for UI
		if hasattr(frappe.local, 'form_dict'):
			frappe.msgprint(f"Processing {len(leads)} leads...", alert=True)
		else:
			print(f"Processing {len(leads)} leads...")
		
		for lead in leads:
			try:
				lead_name = lead.name
				current_owner = lead.lead_owner
				
				# Get assigned user from _assign field
				assigned_user = None
				if lead.get("_assign"):
					try:
						assigned_users = json.loads(lead._assign) if isinstance(lead._assign, str) else lead._assign
						if assigned_users and len(assigned_users) > 0:
							assigned_user = assigned_users[0]
					except:
						pass
				
				# Determine target owner
				if assigned_user and frappe.db.exists("User", assigned_user):
					target_owner = assigned_user
				else:
					target_owner = "Administrator"
				
				# Get owner name
				if target_owner != "Administrator":
					user_doc = frappe.get_doc("User", target_owner)
					owner_name = user_doc.full_name or user_doc.name
				else:
					owner_name = "Administrator"
				
				# Update if different
				update_fields = {}
				if current_owner != target_owner:
					update_fields["lead_owner"] = target_owner
				
				# Check if lead_owner_name field exists
				lead_meta = frappe.get_meta("Lead")
				if lead_meta.has_field("lead_owner_name"):
					current_owner_name = frappe.db.get_value("Lead", lead_name, "lead_owner_name")
					if current_owner_name != owner_name:
						update_fields["lead_owner_name"] = owner_name
				
				if update_fields:
					frappe.db.set_value("Lead", lead_name, update_fields)
					updated_count += 1
				else:
					skipped_count += 1
				
				# Commit every 100 records
				if (updated_count + skipped_count) % 100 == 0:
					frappe.db.commit()
					
			except Exception as e:
				error_count += 1
				frappe.log_error(
					message=f"Error updating lead {lead.name}: {str(e)}\n{frappe.get_traceback()}",
					title="Error syncing lead owner"
				)
				continue
		
		# Final commit
		frappe.db.commit()
		
		message = f"""
		Sync completed!
		- Updated: {updated_count} leads
		- Skipped (already correct): {skipped_count} leads
		- Errors: {error_count} leads
		"""
		
		# Use print for console compatibility, msgprint for UI
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
			title="Error syncing all leads owner"
		)
		# Use print for console compatibility, msgprint for UI
		if hasattr(frappe.local, 'form_dict'):
			frappe.msgprint(f"Error: {str(e)}", alert=True, indicator="red")
		else:
			print(f"Error: {str(e)}")
		return {"success": False, "message": str(e)}

