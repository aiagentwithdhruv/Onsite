"""Rep contact mapping for WhatsApp report delivery.

Add/remove reps here. Phone format: country code + number, no +.
"""

REP_CONTACTS = {
    # Sales Reps (deal_owner field in CRM)
    "Anjali Bajaj": {"phone": "917020774603", "name": "Anjali"},
    "Sunil Demo": {"phone": "919289602555", "name": "Sunil"},
    "Bhavya Pattegudde Janapp": {"phone": "919900425676", "name": "Bhavya"},  # WA number; calling: 9971010837
    "Mohan C": {"phone": "918220494443", "name": "Mohan"},
    "Gayatri Surlkar": {"phone": "919993786319", "name": "Gayatri"},
    "Shailendra Gour": {"phone": "919589613771", "name": "Shailendra"},
    "Amit Balasaheb Udagatti": {"phone": "918762879435", "name": "Amit U"},  # WA+calling; alt calling: 919958052740
    "Hitangi": {"phone": "919082286699", "name": "Hitangi"},
    "Amit Kumar": {"phone": "916263582436", "name": "Amit K"},
    "Desi Yulia": {"phone": "", "name": "Desi"},  # no number provided yet
    # Managers
    "Dhruv": {"phone": "918770101822", "name": "Dhruv"},
    "Sumit": {"phone": "918291400026", "name": "Sumit"},
}

# Pre-sales team
PRESALES_CONTACTS = {
    "Jyoti": {"phone": "918528001207", "name": "Jyoti"},
    "Shruti": {"phone": "919084525155", "name": "Shruti"},
    "Chadni": {"phone": "", "name": "Chadni"},  # no number provided yet
}

# Other team members
OTHER_CONTACTS = {
    "Varsha Kumari": {"phone": "919625647380", "name": "Varsha"},
}

# Managers receive Team Overview + Hygiene Report Card
MANAGER_PHONES = ["918770101822", "918291400026"]  # Dhruv + Sumit

# Monthly demo target
DEMO_TARGET = 400
