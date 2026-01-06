# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

"""
Test script to verify Lead Owner syncs with Assigned To field.
Run with: bench --site [site-name] execute zoho_integration.test_lead_owner_sync.test_lead_owner_sync
"""

import frappe
import json

def test_lead_owner_sync():
	"""Test that Lead Owner syncs with Assigned To"""
	
	print("\n" + "="*50)
	print("Testing Lead Owner Sync with Assigned To")
	print("="*50 + "\n")
	
	# Test 1: Create lead with assignment rule
	print("Test 1: Creating lead with assignment rule...")
	lead = frappe.get_doc({
		"doctype": "Lead",
		"organization_name": "Auto Test Company",
		"first_name": "Auto",
		"last_name": "Test",
		"source": "Advertisement"  # Use a source that has assignment rule
	})
	lead.insert()
	lead.reload()
	
	# Check if assigned
	if lead._assign:
		assigned_users = json.loads(lead._assign) if isinstance(lead._assign, str) else lead._assign
		if assigned_users:
			if lead.lead_owner == assigned_users[0]:
				print(f"✓ PASS: Lead Owner '{lead.lead_owner}' matches assigned user '{assigned_users[0]}'")
			else:
				print(f"✗ FAIL: Lead Owner '{lead.lead_owner}' does not match assigned user '{assigned_users[0]}'")
				return False
		else:
			if lead.lead_owner == "Administrator":
				print("✓ PASS: Lead Owner is Administrator (no assignment)")
			else:
				print(f"✗ FAIL: Lead Owner should be Administrator but is '{lead.lead_owner}'")
				return False
	else:
		if lead.lead_owner == "Administrator":
			print("✓ PASS: Lead Owner is Administrator (no assignment)")
		else:
			print(f"✗ FAIL: Lead Owner should be Administrator but is '{lead.lead_owner}'")
			return False
	
	# Test 2: Manually assign
	print("\nTest 2: Manually assigning lead...")
	# Get first available user (not Administrator)
	users = frappe.get_all("User", filters={"enabled": 1, "name": ["!=", "Administrator"]}, limit=1)
	if users:
		test_user = users[0].name
		lead._assign = json.dumps([test_user])
		lead.save()
		lead.reload()
		
		if lead.lead_owner == test_user:
			print(f"✓ PASS: Lead Owner '{lead.lead_owner}' synced after manual assignment")
		else:
			print(f"✗ FAIL: Lead Owner '{lead.lead_owner}' should be '{test_user}'")
			# Cleanup
			frappe.delete_doc("Lead", lead.name, force=1)
			return False
	else:
		print("⚠ SKIP: No users available for testing")
	
	# Test 3: Remove assignment
	print("\nTest 3: Removing assignment...")
	lead._assign = None
	lead.save()
	lead.reload()
	
	if lead.lead_owner == "Administrator":
		print("✓ PASS: Lead Owner set to Administrator after removing assignment")
	else:
		print(f"✗ FAIL: Lead Owner should be Administrator but is '{lead.lead_owner}'")
		# Cleanup
		frappe.delete_doc("Lead", lead.name, force=1)
		return False
	
	# Cleanup
	print("\nCleaning up test lead...")
	frappe.delete_doc("Lead", lead.name, force=1)
	
	print("\n" + "="*50)
	print("✓ All tests passed!")
	print("="*50 + "\n")
	return True

if __name__ == "__main__":
	test_lead_owner_sync()

