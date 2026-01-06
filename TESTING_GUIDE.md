# Testing Guide: Lead Owner Sync with Assigned To

This guide explains how to test the implementation that syncs Lead Owner with Assigned To field.

## Prerequisites

1. Apply the migrations:
```bash
cd /home/frappe/frappe-bench
bench migrate
bench restart
```

2. Ensure you have:
   - At least 2 users in the system (for round robin testing)
   - An "Intozi CRM Rule" configured with assignment rules
   - Assignment Rules created for Lead sources

## Testing Methods

### Method 1: Manual Testing via UI

#### Test 1: Create a New Lead and Verify Assignment

1. **Create a new Lead:**
   - Go to CRM > Lead > New
   - Fill in required fields:
     - Organization Name: "Test Company"
     - First Name: "Test"
     - Last Name: "User"
     - Source: Select a source that has an assignment rule configured (e.g., "Advertisement")
   - Click "Save"

2. **Verify Assignment:**
   - Check the left sidebar - you should see "Assigned To" with a user
   - Check the "Lead Owner" field in the Details section
   - **Expected Result:** Lead Owner should match the Assigned To user

3. **If no assignment:**
   - If the lead is not assigned to anyone, Lead Owner should be "Administrator"

#### Test 2: Update Existing Lead Assignment

1. **Manually assign a lead:**
   - Open an existing Lead
   - In the left sidebar, click the "+" next to "Assigned To"
   - Select a user (e.g., "RD" or any other user)
   - Save the lead

2. **Verify Lead Owner:**
   - Check the "Lead Owner" field
   - **Expected Result:** Lead Owner should automatically update to match the Assigned To user

#### Test 3: Remove Assignment

1. **Remove assignment:**
   - Open a Lead that has an assignment
   - Remove the user from "Assigned To" (click the X or remove)
   - Save the lead

2. **Verify Lead Owner:**
   - **Expected Result:** Lead Owner should automatically change to "Administrator"

### Method 2: Console Testing

Run these commands in Frappe console to test programmatically:

```bash
cd /home/frappe/frappe-bench
bench --site [your-site-name] console
```

#### Test 1: Create Lead and Check Assignment

```python
import frappe
import json

# Create a test lead
lead = frappe.get_doc({
    "doctype": "Lead",
    "organization_name": "Test Company Console",
    "first_name": "Test",
    "last_name": "Console",
    "source": "Advertisement"  # Use a source with assignment rule
})
lead.insert()

# Reload to get assignment
lead.reload()

# Check assignment
print(f"Lead: {lead.name}")
print(f"Assigned To (_assign): {lead._assign}")
print(f"Lead Owner: {lead.lead_owner}")

# Parse _assign if it exists
if lead._assign:
    assigned_users = json.loads(lead._assign) if isinstance(lead._assign, str) else lead._assign
    if assigned_users:
        print(f"First Assigned User: {assigned_users[0]}")
        print(f"Lead Owner matches: {lead.lead_owner == assigned_users[0]}")
else:
    print("No assignment - Lead Owner should be Administrator")
    print(f"Lead Owner is Administrator: {lead.lead_owner == 'Administrator'}")
```

#### Test 2: Manually Assign and Verify Sync

```python
import frappe
import json

# Get an existing lead
lead_name = "LEAD-25/12-0065"  # Replace with actual lead name
lead = frappe.get_doc("Lead", lead_name)

# Get a test user (replace with actual username)
test_user = "rd@example.com"  # Replace with actual user email

# Assign the lead
lead._assign = json.dumps([test_user])
lead.save()

# Reload and check
lead.reload()
print(f"Assigned To: {lead._assign}")
print(f"Lead Owner: {lead.lead_owner}")
print(f"Match: {lead.lead_owner == test_user}")
```

#### Test 3: Remove Assignment

```python
import frappe

# Get an existing lead
lead_name = "LEAD-25/12-0065"  # Replace with actual lead name
lead = frappe.get_doc("Lead", lead_name)

# Remove assignment
lead._assign = None
lead.save()

# Reload and check
lead.reload()
print(f"Assigned To: {lead._assign}")
print(f"Lead Owner: {lead.lead_owner}")
print(f"Is Administrator: {lead.lead_owner == 'Administrator'}")
```

### Method 3: Test via Zoho Webhook (Real Integration)

1. **Trigger a webhook from Zoho:**
   - This will create a lead through the `receive_lead()` function
   - The lead will go through the assignment rule
   - Lead Owner should sync automatically

2. **Check the Lead Integration Log:**
   - Go to Zoho Integration > Lead Integration Log
   - Find the latest log entry
   - Click "Retry" if status is "Pending"
   - Check the created Lead

3. **Verify in Lead:**
   - Open the created Lead
   - Check both "Assigned To" and "Lead Owner"
   - They should match

### Method 4: Automated Test Script

Create a test file to run automated tests:

```python
# test_lead_owner_sync.py
import frappe
import json

def test_lead_owner_sync():
    """Test that Lead Owner syncs with Assigned To"""
    
    # Test 1: Create lead with assignment rule
    lead = frappe.get_doc({
        "doctype": "Lead",
        "organization_name": "Auto Test Company",
        "first_name": "Auto",
        "last_name": "Test",
        "source": "Advertisement"
    })
    lead.insert()
    lead.reload()
    
    # Check if assigned
    if lead._assign:
        assigned_users = json.loads(lead._assign) if isinstance(lead._assign, str) else lead._assign
        if assigned_users:
            assert lead.lead_owner == assigned_users[0], \
                f"Lead Owner {lead.lead_owner} should match assigned user {assigned_users[0]}"
            print("✓ Test 1 Passed: Lead Owner matches Assigned To")
        else:
            assert lead.lead_owner == "Administrator", \
                "Lead Owner should be Administrator when no assignment"
            print("✓ Test 1 Passed: Lead Owner is Administrator (no assignment)")
    else:
        assert lead.lead_owner == "Administrator", \
            "Lead Owner should be Administrator when no assignment"
        print("✓ Test 1 Passed: Lead Owner is Administrator (no assignment)")
    
    # Test 2: Manually assign
    test_user = "rd@example.com"  # Replace with actual user
    if frappe.db.exists("User", test_user):
        lead._assign = json.dumps([test_user])
        lead.save()
        lead.reload()
        assert lead.lead_owner == test_user, \
            f"Lead Owner {lead.lead_owner} should match {test_user}"
        print("✓ Test 2 Passed: Lead Owner synced after manual assignment")
    
    # Test 3: Remove assignment
    lead._assign = None
    lead.save()
    lead.reload()
    assert lead.lead_owner == "Administrator", \
        "Lead Owner should be Administrator after removing assignment"
    print("✓ Test 3 Passed: Lead Owner set to Administrator after removing assignment")
    
    # Cleanup
    frappe.delete_doc("Lead", lead.name, force=1)
    print("✓ All tests passed!")

if __name__ == "__main__":
    test_lead_owner_sync()
```

Run it:
```bash
bench --site [your-site-name] execute zoho_integration.test_lead_owner_sync.test_lead_owner_sync
```

## Troubleshooting

### Issue: Lead Owner not syncing

1. **Check hooks are loaded:**
```python
import frappe
print(frappe.get_hooks("doc_events"))
```

2. **Check if function is being called:**
   - Add print statements in `lead_utils.py` to see if function is triggered
   - Check Error Log for any errors

3. **Verify assignment rule is working:**
   - Go to Setup > Assignment Rule
   - Check if rules exist for your Lead sources
   - Verify they are enabled

4. **Check field permissions:**
   - Ensure users have write permission on `lead_owner` field

### Issue: Recursion errors

- The code includes recursion protection
- If you see recursion errors, check the `sync_lead_owner_in_progress` flag logic

## Expected Behavior Summary

✅ **When a Lead is assigned to a user:**
- Lead Owner = Assigned User

✅ **When a Lead has no assignment:**
- Lead Owner = "Administrator"

✅ **When assignment changes:**
- Lead Owner automatically updates to match

✅ **Works for:**
- New leads created via UI
- New leads created via Zoho webhook
- Existing leads that get reassigned
- Leads with assignment removed

