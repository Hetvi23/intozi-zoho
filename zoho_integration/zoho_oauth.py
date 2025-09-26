import frappe
import requests
from datetime import datetime, timedelta

#Initaial step to Get the access token One time use when doing Configrationn of the App Zoho integration
CLIENT_ID = "1000.ZP9OZ4Y4YID6Y3DRHZVQK06W12G24S"
CLIENT_SECRET = "3c18ab8c17120c1d4b06e06b1271901a2812781a46"
REDIRECT_URI = "http://65.20.89.49:8003/api/method/zoho_integration.zoho_oauth.zoho_oauth_callback"

@frappe.whitelist(allow_guest=True)
def zoho_oauth_callback():
    """Receive OAuth code from Zoho and save tokens in Zoho Integration Settings"""
    code = frappe.form_dict.get("code")
    if not code:
        return "No authorization code received"

    url = "https://accounts.zoho.in/oauth/v2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    response = requests.post(url, data=payload)
    data = response.json()

    if data.get("access_token"):
        # Try to fetch existing Doc
        try:
            doc = frappe.get_doc("Zoho Integration Settings")
            doc.access_token = data["access_token"]
            doc.refresh_token = data["refresh_token"]
            doc.token_expiry = datetime.now() + timedelta(seconds=int(data.get("expires_in", 3600)))
            doc.save(ignore_permissions=True)
        except frappe.DoesNotExistError:
            # If it doesn't exist, create a new one
            doc = frappe.get_doc({
                "doctype": "Zoho Integration Settings",
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "token_expiry": datetime.now() + timedelta(seconds=int(data.get("expires_in", 3600)))
            })
            doc.insert(ignore_permissions=True)

        frappe.db.commit()
        return "Tokens saved successfully"
    else:
        return data
