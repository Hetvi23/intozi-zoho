import frappe
import json
import requests
from datetime import datetime, timedelta
from frappe.utils import get_datetime

CLIENT_ID = "1000.ZP9OZ4Y4YID6Y3DRHZVQK06W12G24S"
CLIENT_SECRET = "3c18ab8c17120c1d4b06e06b1271901a2812781a46"
ZOHO_TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"

# to refresh Token
def get_access_token():
    """Return a valid Zoho access token. Refresh if expired."""
    try:
        settings = frappe.get_doc("Zoho Integration Settings")
    except frappe.DoesNotExistError:
        frappe.throw("Zoho Integration Settings not found. Get initial tokens first.")

    # Parse token_expiry safely
    token_expiry = get_datetime(settings.token_expiry) if settings.token_expiry else None

    # Refresh token if expired or missing
    if not token_expiry or token_expiry < datetime.now():
        payload = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": settings.refresh_token
        }
        response = requests.post(ZOHO_TOKEN_URL, data=payload)
        data = response.json()

        if data.get("access_token"):
            settings.access_token = data["access_token"]
            settings.token_expiry = (datetime.now() + timedelta(seconds=int(data.get("expires_in", 3600)))).strftime('%Y-%m-%d %H:%M:%S')
            settings.save(ignore_permissions=True)
            frappe.db.commit()
        else:
            frappe.throw(f"Failed to refresh Zoho token: {data}")

    return settings.access_token

#to update the lead status to the zoho
@frappe.whitelist()
def update_zoho_lead_status(zoho_lead_id, status):
    """
    Update Lead Sync Status in Zoho CRM.
    """
    try:
        access_token = get_access_token()
        url = f"https://www.zohoapis.in/crm/v2/Leads/{zoho_lead_id}"
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        payload = {
            "data": [
                {
                    "id": zoho_lead_id,
                    "Lead_Sync_Status": status
                }
            ]
        }

        response = requests.put(url, json=payload, headers=headers)
        return response.json()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), title="Zoho Lead Sync Status Update Failed")
        return {"status": "error", "message": str(e)}

#to make entry in the log
@frappe.whitelist(allow_guest=True)
def receive_lead():
    try:
        data = frappe.request.get_json(silent=True)

        # If not JSON, fallback to raw/form
        if not data:
            raw_data = frappe.local.request.get_data(as_text=True)
            try:
                data = json.loads(raw_data) if raw_data else {}
            except:
                data = frappe.local.form_dict or {}

        integration_id = data.get("id")
        lead_sync_status = data.get("Lead_Sync_Status") or "-None-"

        # ✅ Skip if Zoho already marked as synced
        if lead_sync_status in ["Lead Created in ERPNext", "Completed", "Failed"]:
            return {"status": "skipped", "message": f"Webhook ignored. Lead already processed in Zoho ({lead_sync_status})."}

        # ✅ Skip if ERPNext Lead already has sync flag
        if integration_id and frappe.db.exists("Lead", {"custom_integration_lead_id": integration_id, "custom_integration_sync_done": 1}):
            return {"status": "skipped", "message": f"Webhook ignored. Lead already synced in ERPNext (Zoho ID {integration_id})."}

        # Save into Lead Integration Log
        doc = frappe.get_doc({
            "doctype": "Lead Integration Log",
            "status": "Pending",
            "data": json.dumps(data),
            "integration_id": integration_id,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "message": "Lead logged and queued"}

    except Exception:
        frappe.log_error(message=frappe.get_traceback(), title="Zoho Webhook Error")
        return {"status": "error", "message": "Something went wrong"}

# to create the lead by the cron-job of pending leads
def retry_pending_leads():
    """
    Fetch all pending Lead Integration Logs and process them.
    Called every 2 minutes by cron.
    """
    pending_logs = frappe.get_all(
        "Lead Integration Log",
        filters={"status": "Pending"},
        fields=["name"]
    )

    for log in pending_logs:
        try:
            process_webhook_lead(log["name"])
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Retry Pending Lead Failed")


#new code
@frappe.whitelist()
def process_webhook_lead(log_name):
    """
    Take Lead Integration Log payload and create/update ERPNext Lead
    """
    log = frappe.get_doc("Lead Integration Log", log_name)
    payload = json.loads(log.data or "{}")
    integration_id = payload.get("id")

    try:
        # 🔹 Check if Lead already exists in ERPNext (avoid duplicates)
        existing_lead = None
        if integration_id:
            existing_lead = frappe.db.exists("Lead", {"custom_integration_lead_id": integration_id})

        if existing_lead:
            log.status = "Success" or "Failed"
            log.response_message = f"Lead already exists in ERPNext (Zoho ID {integration_id})"
            log.lead = existing_lead
            log.save(ignore_permissions=True)
            frappe.db.commit()
            return

        # 🔹 Create or update lead
        lead = upsert_zoho_lead(payload)

        # 🔹 Update the log with ERPNext Lead ID
        log.status = "Success"
        log.response_message = f"Lead created: {lead.name}"
        log.lead = lead.name       # ✅ Save reference to created lead
        log.save(ignore_permissions=True)
        frappe.db.commit()

        # 🔹 Optionally sync back to Zoho
        if integration_id:
            update_zoho_lead_status(integration_id, "Lead Created in ERPNext")

    except Exception:
        log.status = "Failed"
        log.response_message = frappe.get_traceback()
        log.save(ignore_permissions=True)
        frappe.db.commit()

def safe_set_value(doc, field, value, mapping=None, default=None):
    """Helper to safely set mapped values for Link/Select fields"""
    if mapping:
        value = mapping.get(value, default)
    if value:
        doc.set(field, value)

def map_employees_to_range(value):
    """Convert numeric employee count from Zoho into ERPNext range"""
    EMPLOYEE_RANGE_MAP = [
        (1, 10, "1-10"),
        (11, 50, "11-50"),
        (51, 200, "51-200"),
        (201, 500, "201-500"),
        (501, 1000, "501-1000"),
        (1001, float("inf"), "1000+"),
    ]
    try:
        num = int(value)
        for low, high, label in EMPLOYEE_RANGE_MAP:
            if low <= num <= high:\
                return label
    except Exception:
        return None
    return None



def upsert_zoho_lead(data):
    """Create or update ERPNext Lead from Zoho payload"""

    email = data.get("email")
    phone = data.get("phone")
    mobile = data.get("mobile")
    integration_id = data.get("id")  # Zoho Lead ID

    # --- Try to find existing lead
    lead = None
    if integration_id:
        lead_name = frappe.db.exists("Lead", {"custom_integration_lead_id": integration_id})
        if lead_name:
            lead = frappe.get_doc("Lead", lead_name)
    elif email:
        lead_name = frappe.db.exists("Lead", {"email_id": email})
        if lead_name:
            lead = frappe.get_doc("Lead", lead_name)
    elif mobile:
        lead_name = frappe.db.exists("Lead", {"mobile_no": mobile})
        if lead_name:
            lead = frappe.get_doc("Lead", lead_name)
    elif phone:
        lead_name = frappe.db.exists("Lead", {"phone": phone})
        if lead_name:
            lead = frappe.get_doc("Lead", lead_name)

    if not lead:
        lead = frappe.get_doc({"doctype": "Lead"})

    # --- Always set Zoho ID
    if integration_id:
        lead.custom_integration_lead_id = integration_id

    # --- Lookup maps
    SALUTATION_MAP = {"Mr.": "Mr", "Mrs.": "Mrs", "Ms.": "Ms", "Dr.": "Dr", "Prof.": "Prof", "-None-": None}
    STATUS_MAP = {
        "-None-": "Open", "Attempted to Contact": "Replied", "Contact in Future": "Open",
        "Contacted": "Replied", "Junk Lead": "Do Not Contact", "Lost Lead": "Lost Quotation",
        "Not Contacted": "Open", "Pre-Qualified": "Interested", "Not Qualified": "Do Not Contact",
    }
    SOURCE_MAP = {
        "-None-": None, "Advertisement": "Advertisement", "Cold Call": "Cold Call",
        "Employee Referral": "Employee Referral", "External Referral": "External Referral",
        "Online Store": "Online Store", "Partner": "Partner", "Public Relations": "Public Relations",
        "Sales Email Alias": "Sales Email", "Seminar Partner": "Seminar Partner",
        "Internal Seminar": "Seminar Partner", "Trade Show": "Exhibition", "Web Download": "Website",
        "Web Research": "Website", "Chat": "Chat", "X (Twitter)": "Twitter", "Facebook": "Facebook",
    }
    INDUSTRY_MAP = {
        "-None-": None, "Government/Military": "Defense", "Large Enterprise": "Manufacturing",
        "ERP (Enterprise Resource Planning)": "Software", "ManagementISV": "Consulting",
        "Management ISV": "Consulting", "Non-management ISV": "Software",
        "MSP (Management Service Provider)": "Service", "Service Provider": "Service",
        "Small/Medium Enterprise": "Manufacturing", "Systems Integrator": "Consulting",
        "Wireless Industry": "Telecommunications", "Data/Telecom OEM": "Telecommunications",
        "Optical Networking": "Telecommunications", "Storage Equipment": "Electronics",
        "Storage Service Provider": "Service", "ASP (Application Service Provider)": "Technology",
    }

    # --- Load mapping doc
    mapping_doc = frappe.get_doc("Lead Field Mapping", "Zoho to ERPNext")

    for row in mapping_doc.lead_field_mapping_details:
        erp_field, external_field = row.erpnext_field, row.external_field
        if not erp_field or not external_field:
            continue

        value = data.get(external_field)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()

        # --- Special cases
        if erp_field == "salutation":
            value = SALUTATION_MAP.get(value)
        elif erp_field == "lead_owner":
            if not frappe.db.exists("User", value):
                value = frappe.session.user
        elif erp_field == "status":
            value = STATUS_MAP.get(value, "Open")
        elif erp_field == "source":
            value = SOURCE_MAP.get(value, "Advertisement")
        elif erp_field == "industry":
            mapped_value = INDUSTRY_MAP.get(value)
            if mapped_value:
                value = mapped_value
            if value and not frappe.db.exists("Industry Type", value):
                frappe.get_doc({"doctype": "Industry Type", "industry": value}).insert(ignore_permissions=True)
        elif erp_field == "no_of_employees":
            value = map_employees_to_range(value)
        elif erp_field == "annual_revenue":
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0

        lead.set(erp_field, value)

    # --- Ensure lead_name
    if not lead.lead_name:
        lead.lead_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "Unknown"

    # --- Save lead initially
    lead.custom_integration_sync_done = 0
    try:
        if lead.is_new():
            lead.insert(ignore_permissions=True, ignore_version=True)
        else:
            lead.save(ignore_permissions=True, ignore_version=True)
    except Exception:
        frappe.log_error(message=frappe.get_traceback(), title="ERPNext Lead Save Failed")
        raise

    frappe.db.commit()

    # --- Update Zoho and mark sync done
    if integration_id:
        try:
            update_zoho_lead_status(integration_id, "Completed")

            # ✅ use set_value to avoid TimestampMismatchError
            frappe.db.set_value("Lead", lead.name, "custom_integration_sync_done", 1)
            frappe.db.commit()
        except Exception:
            frappe.log_error(message=frappe.get_traceback(), title="Zoho Lead Status Update Failed")
            frappe.db.set_value("Lead", lead.name, "custom_integration_sync_done", 0)
            frappe.db.commit()

    return lead
