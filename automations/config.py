"""Shared config for all Onsite automations."""

# Zoho CRM
ZOHO_CLIENT_ID = "1000.D98P3ZGFZFNRDUQCA5W3BU754H93RD"
ZOHO_CLIENT_SECRET = "184564298f04d2fdf7d88284b066379be4908ddbb2"
ZOHO_REFRESH_TOKEN = "1000.a58fce66a90c3b0c05fd0abae49a2484.f3b7bf8173c395f6a58a8d1430b912d0"
ZOHO_TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"
ZOHO_API_BASE = "https://www.zohoapis.in/crm/v7"

# Gallabox WhatsApp
GALLABOX_API_KEY = "699d5e2ebdf70f643a41e774"
GALLABOX_API_SECRET = "be2886a0ce0f4a6c990c1c59df972fc9"
GALLABOX_CHANNEL_ID = "642ead91fe1098cbbd157509"
GALLABOX_URL = "https://server.gallabox.com/devapi/messages/whatsapp"

# Facebook Ads
FB_ACCESS_TOKEN = ""  # Set from env if needed
FB_AD_ACCOUNT_ID = "act_3176065209371338"

# Team directory (except Sumit & Akshansh — managers get separate reports)
SALES_REPS = {
    "Sunil": "919289602555",
    "Anjali": "917020774603",
    "Bhavya": "919900425676",
    "Mohan": "918220494443",
    "Gayatri": "919993786319",
    "Shailendra": "919589613771",
    "Amit U": "918762879435",
    "Hitangi": "919082286699",
    "Amit Kumar": "916263582436",
}

PRE_SALES = {
    "Jyoti": "918528001207",
    "Shruti": "919084525155",
}

MANAGERS = {
    "Sumit": "918291400026",
    "Akshansh": "919654225317",
    "Dhruv": "918770101822",
}

ALL_TEAM = {**SALES_REPS, **PRE_SALES}

# CRM field mappings
CRM_OWNER_MAP = {
    "Sunil Demo": "Sunil",
    "Anjali Bajaj": "Anjali",
    "Bhavya Pattegudde Janappa": "Bhavya",
    "Bhavya P Janappa": "Bhavya",
    "Mohan C": "Mohan",
    "Gayatri Surlkar": "Gayatri",
    "Gayatri": "Gayatri",
    "Shailendra Gour": "Shailendra",
    "Shailendra": "Shailendra",
    "Amit B Udagatti": "Amit U",
    "Amit Udagatti": "Amit U",
    "Hitangi Arora": "Hitangi",
    "Hitangi": "Hitangi",
    "Amit Kumar": "Amit Kumar",
    "Desi Yulia": "Desi",
    "Jyoti": "Jyoti",
    "Shruti": "Shruti",
    "Chadni": "Chadni",
}
