from flask import Flask, request, jsonify
import requests
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# --------------------------
# 🔐 YOUR ZOHO CONFIG
# --------------------------
ZOHO_CLIENT_ID     = "1000.INUAI1YA2Z9B9S0ZDYRIFPKAX01Q0R"
ZOHO_CLIENT_SECRET = "c0088204c5d49eb671c6ecba8139a26735f4ab71bb"
ZOHO_REFRESH_TOKEN = "1000.a2f525252fcec911b6b7d4bd086f7933.ab7cdb9b1a651ee4f349b6503cea2683"
ZOHO_REGION        = "eu"
ZOHO_SHEET_ID      = "h0ncucf6bf0e57ff743828afbf8e648600c59"
ZOHO_WORKSHEET     = "Website_Leads"

# --------------------------
# 📧 EMAIL SETUP
# --------------------------
SMTP_SERVER   = "smtp.zoho.eu"
SMTP_PORT     = 465
SMTP_USER     = "henryromanenko@bridgfunderlondon.co.uk"
SMTP_PASSWORD = "aR4dv9A860L0"  # Your Zoho app password

# --------------------------
# 🛠️ HELPER FUNCTIONS
# --------------------------
def get_zoho_access_token():
    res = requests.post(
        f"https://accounts.zoho.{ZOHO_REGION}/oauth/v2/token",
        data={
            "grant_type": "refresh_token",
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "refresh_token": ZOHO_REFRESH_TOKEN
        },
        timeout=15
    )
    data = res.json()
    if "access_token" not in data:
        raise Exception(f"Auth failed: {data}")
    return data["access_token"]

def append_to_zoho_sheet(row):
    token = get_zoho_access_token()
    url = f"https://sheet.zoho.{ZOHO_REGION}/api/v2/{ZOHO_SHEET_ID}"
    payload = {"worksheet_name": ZOHO_WORKSHEET, "data": [row]}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    return r.status_code, r.text

def send_email(to, subject, html):
    msg = MIMEMultipart("alternative")
    msg["From"] = "BridgFunder London <henryromanenko@bridgfunderlondon.co.uk>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Reply-To"] = "contact@bridgfunderlondon.co.uk"
    msg.attach(MIMEText("Please enable HTML to view this email.", "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

# --------------------------
# 🚀 API ENDPOINT
# --------------------------
@app.route("/submit-lead", methods=["POST", "OPTIONS"])
def submit_lead():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200, headers

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400, headers

        # Exact column order matching your sheet
        new_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("fullName", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("category", ""),
            data.get("goal", ""),
            data.get("propertyValue", ""),
            data.get("loanAmount", ""),
            data.get("currentLender", ""),
            data.get("additionalInfo", ""),
            "New Lead"
        ]

        status, resp = append_to_zoho_sheet(new_row)
        if status not in (200, 201):
            raise Exception(f"Sheet error: {status} {resp}")

        # Send emails
        client_html = f"""
        <!DOCTYPE html><html><body style="margin:0; padding:0; background:#F4F7F8; font-family:Arial, sans-serif;">
        <table width="100%" cellpadding="40" cellspacing="0"><tr><td align="center">
        <table style="max-width:600px; background:#fff; border-radius:12px; border:1px solid #E2E8F0;">
        <tr><td style="padding:30px; border-top:6px solid #0F172A; border-bottom:2px solid #FFD700; text-align:center;">
        <h2 style="margin:0; color:#0F172A;">Funding Enquiry Received</h2></tr>
        <tr><td style="padding:30px; color:#475569;">
        <p>Dear {data.get('fullName', '')},</p>
        <p>Thank you for your enquiry — we have received your details and will review them shortly.</p>
        <p>A senior underwriter will contact you within 24 business hours.</p>
        <p>Best regards,<br><strong>The BridgFunder Team</strong></p></td></tr></table></td></tr></table>
        </body></html>
        """

        admin_html = f"""
        <div style="font-family:Arial, sans-serif; max-width:600px; border:1px solid #E2E8F0; border-radius:8px;">
        <div style="background:#0F172A; padding:15px; text-align:center;">
        <h2 style="color:#FFD700; margin:0;">NEW FUNDING LEAD</h2></div>
        <table width="100%" cellpadding="12" cellspacing="0">
        <tr><td><strong>Name:</strong></td><td>{data.get('fullName')}</td></tr>
        <tr><td><strong>Email:</strong></td><td>{data.get('email')}</td></tr>
        <tr><td><strong>Phone:</strong></td><td>{data.get('phone')}</td></tr>
        <tr><td><strong>Profile:</strong></td><td>{data.get('category')}</td></tr>
        <tr><td><strong>Requirement:</strong></td><td>{data.get('goal')}</td></tr>
        <tr><td><strong>Property Value:</strong></td><td>£{data.get('propertyValue')}</td></tr>
        <tr><td><strong>Loan Required:</strong></td><td>£{data.get('loanAmount')}</td></tr>
        <tr><td><strong>Current Lender:</strong></td><td>{data.get('currentLender') or 'None'}</td></tr>
        <tr><td><strong>Notes:</strong></td><td>{data.get('additionalInfo') or 'None'}</td></tr>
        </table></div>
        """

        send_email(data.get("email", ""), "✅ Funding Enquiry Received", client_html)
        send_email("henryromanenko@bridgfunderlondon.co.uk, contact@bridgfunderlondon.co.uk", f"📩 New Lead: {data.get('fullName')}", admin_html)

        return jsonify({"status": "success", "message": "Lead saved + emails sent"}), 200, headers

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500, headers

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
