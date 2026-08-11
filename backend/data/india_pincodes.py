"""
india_pincodes.py
─────────────────
Local Indian Postal & Geographic Dataset.
Provides offline mapping of 6-digit Indian PIN codes to candidate post offices,
localities, cities, districts, and states without cloud API dependencies.
"""

from typing import Dict, Any, List, Optional

INDIAN_STATES_AND_UTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # Union Territories
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

STATE_ALIASES = {
    "GJ": "Gujarat",
    "MH": "Maharashtra",
    "DL": "Delhi",
    "RJ": "Rajasthan",
    "MP": "Madhya Pradesh",
    "UP": "Uttar Pradesh",
    "KA": "Karnataka",
    "TN": "Tamil Nadu",
    "KL": "Kerala",
    "WB": "West Bengal",
    "HR": "Haryana",
    "PB": "Punjab",
    "AP": "Andhra Pradesh",
    "TG": "Telangana",
    "TS": "Telangana",
    "BR": "Bihar",
    "OR": "Odisha",
    "OD": "Odisha",
    "JH": "Jharkhand",
    "UK": "Uttarakhand",
    "UA": "Uttarakhand",
    "HP": "Himachal Pradesh",
    "JK": "Jammu and Kashmir",
    "CT": "Chhattisgarh",
    "CG": "Chhattisgarh"
}

# Major Exact PIN Code Map (Sampled Across Regions)
EXACT_PIN_DATABASE: Dict[str, Dict[str, Any]] = {
    # Gujarat
    "395006": {"city": "Surat", "district": "Surat", "state": "Gujarat", "post_office": "Varachha Road", "candidate_localities": ["Surat", "Varachha", "Katargam", "Kapodra", "Hirabaug"]},
    "395007": {"city": "Surat", "district": "Surat", "state": "Gujarat", "post_office": "SVNIT Surat", "candidate_localities": ["Surat", "Piplod", "Dumas Road", "Vesu"]},
    "395003": {"city": "Surat", "district": "Surat", "state": "Gujarat", "post_office": "Surat Main", "candidate_localities": ["Surat", "Athwa", "Chowk Bazar", "Nanpura"]},
    "380001": {"city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "post_office": "Ahmedabad GPO", "candidate_localities": ["Ahmedabad", "Bhadra", "Kalupur", "Lal Darwaja"]},
    "380015": {"city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "post_office": "IIM Ahmedabad", "candidate_localities": ["Ahmedabad", "Vastrapur", "Bodakdev", "Satellite"]},
    "390001": {"city": "Vadodara", "district": "Vadodara", "state": "Gujarat", "post_office": "Vadodara GPO", "candidate_localities": ["Vadodara", "Alkapuri", "Raopura", "Sayajiganj"]},
    "360001": {"city": "Rajkot", "district": "Rajkot", "state": "Gujarat", "post_office": "Rajkot GPO", "candidate_localities": ["Rajkot", "Yagnik Road", "Race Course", "Kalawad Road"]},
    
    # Maharashtra
    "400001": {"city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "post_office": "Mumbai GPO", "candidate_localities": ["Mumbai", "Fort", "Colaba", "Marine Lines"]},
    "400050": {"city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "post_office": "Bandra West", "candidate_localities": ["Mumbai", "Bandra", "Pali Hill", "Carter Road"]},
    "411001": {"city": "Pune", "district": "Pune", "state": "Maharashtra", "post_office": "Pune GPO", "candidate_localities": ["Pune", "Camp", "Koregaon Park", "Shivajinagar"]},
    "440001": {"city": "Nagpur", "district": "Nagpur", "state": "Maharashtra", "post_office": "Nagpur GPO", "candidate_localities": ["Nagpur", "Sitabuldi", "Dharampeth", "Civil Lines"]},

    # Delhi NCR
    "110001": {"city": "Delhi", "district": "Central Delhi", "state": "Delhi", "post_office": "Connaught Place", "candidate_localities": ["Delhi", "New Delhi", "Connaught Place", "Janpath"]},
    "110016": {"city": "Delhi", "district": "South Delhi", "state": "Delhi", "post_office": "IIT Delhi", "candidate_localities": ["Delhi", "Hauz Khas", "Green Park", "Safdarjung"]},
    "122001": {"city": "Gurgaon", "district": "Gurugram", "state": "Haryana", "post_office": "Gurgaon H.O", "candidate_localities": ["Gurgaon", "Gurugram", "DLF Phase 1", "Cyber City"]},
    "201301": {"city": "Noida", "district": "Gautam Buddha Nagar", "state": "Uttar Pradesh", "post_office": "Noida Sector 16", "candidate_localities": ["Noida", "Sector 18", "Sector 62", "Greater Noida"]},

    # Karnataka
    "560001": {"city": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "post_office": "Bengaluru GPO", "candidate_localities": ["Bengaluru", "Bangalore", "MG Road", "Brigade Road", "Shivajinagar"]},
    "560034": {"city": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "post_office": "Koramangala", "candidate_localities": ["Bengaluru", "Bangalore", "Koramangala", "HSR Layout", "BTM Layout"]},

    # Tamil Nadu
    "600001": {"city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "post_office": "Chennai GPO", "candidate_localities": ["Chennai", "Parrys", "Georgetown", "Royapuram"]},
    "600017": {"city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "post_office": "T Nagar", "candidate_localities": ["Chennai", "T Nagar", "Kodambakkam", "Mambalam"]},

    # Telangana
    "500001": {"city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "post_office": "Hyderabad GPO", "candidate_localities": ["Hyderabad", "Abids", "Nampally", "Koti"]},
    "500081": {"city": "Hyderabad", "district": "Ranga Reddy", "state": "Telangana", "post_office": "Hitech City", "candidate_localities": ["Hyderabad", "Hitech City", "Madhapur", "Gachibowli"]},

    # West Bengal
    "700001": {"city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "post_office": "Kolkata GPO", "candidate_localities": ["Kolkata", "Dalhousie", "BBD Bagh", "Bara Bazar"]},

    # Rajasthan
    "302001": {"city": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "post_office": "Jaipur GPO", "candidate_localities": ["Jaipur", "MI Road", "Johari Bazar", "Pink City"]}
}

# Postal Circle 2-Digit Prefix Fallback Map
POSTAL_PREFIX_MAP: Dict[str, Tuple[str, str, str]] = {
    # Prefix -> (Default City, Default District, State)
    "11": ("Delhi", "Central Delhi", "Delhi"),
    "12": ("Gurgaon", "Gurugram", "Haryana"),
    "13": ("Ambala", "Ambala", "Haryana"),
    "14": ("Chandigarh", "Chandigarh", "Punjab"),
    "15": ("Bhatinda", "Bathinda", "Punjab"),
    "16": ("Chandigarh", "Chandigarh", "Chandigarh"),
    "17": ("Shimla", "Shimla", "Himachal Pradesh"),
    "18": ("Jammu", "Jammu", "Jammu and Kashmir"),
    "19": ("Srinagar", "Srinagar", "Jammu and Kashmir"),
    "20": ("Noida", "Gautam Buddha Nagar", "Uttar Pradesh"),
    "21": ("Allahabad", "Prayagraj", "Uttar Pradesh"),
    "22": ("Lucknow", "Lucknow", "Uttar Pradesh"),
    "23": ("Varanasi", "Varanasi", "Uttar Pradesh"),
    "24": ("Dehradun", "Dehradun", "Uttarakhand"),
    "25": ("Meerut", "Meerut", "Uttar Pradesh"),
    "26": ("Bareilly", "Bareilly", "Uttar Pradesh"),
    "27": ("Gorakhpur", "Gorakhpur", "Uttar Pradesh"),
    "28": ("Agra", "Agra", "Uttar Pradesh"),
    "30": ("Jaipur", "Jaipur", "Rajasthan"),
    "31": ("Udaipur", "Udaipur", "Rajasthan"),
    "32": ("Kota", "Kota", "Rajasthan"),
    "33": ("Bikaner", "Bikaner", "Rajasthan"),
    "34": ("Jodhpur", "Jodhpur", "Rajasthan"),
    "36": ("Rajkot", "Rajkot", "Gujarat"),
    "37": ("Jamnagar", "Jamnagar", "Gujarat"),
    "38": ("Ahmedabad", "Ahmedabad", "Gujarat"),
    "39": ("Surat", "Surat", "Gujarat"),
    "40": ("Mumbai", "Mumbai", "Maharashtra"),
    "41": ("Pune", "Pune", "Maharashtra"),
    "42": ("Nashik", "Nashik", "Maharashtra"),
    "43": ("Aurangabad", "Chhatrapati Sambhajinagar", "Maharashtra"),
    "44": ("Nagpur", "Nagpur", "Maharashtra"),
    "45": ("Indore", "Indore", "Madhya Pradesh"),
    "46": ("Bhopal", "Bhopal", "Madhya Pradesh"),
    "47": ("Gwalior", "Gwalior", "Madhya Pradesh"),
    "48": ("Jabalpur", "Jabalpur", "Madhya Pradesh"),
    "49": ("Raipur", "Raipur", "Chhattisgarh"),
    "50": ("Hyderabad", "Hyderabad", "Telangana"),
    "51": ("Tirupati", "Tirupati", "Andhra Pradesh"),
    "52": ("Vijayawada", "NTR District", "Andhra Pradesh"),
    "53": ("Visakhapatnam", "Visakhapatnam", "Andhra Pradesh"),
    "56": ("Bengaluru", "Bengaluru Urban", "Karnataka"),
    "57": ("Mysuru", "Mysuru", "Karnataka"),
    "58": ("Hubballi", "Dharwad", "Karnataka"),
    "59": ("Belagavi", "Belagavi", "Karnataka"),
    "60": ("Chennai", "Chennai", "Tamil Nadu"),
    "61": ("Thanjavur", "Thanjavur", "Tamil Nadu"),
    "62": ("Madurai", "Madurai", "Tamil Nadu"),
    "63": ("Coimbatore", "Coimbatore", "Tamil Nadu"),
    "64": ("Coimbatore", "Coimbatore", "Tamil Nadu"),
    "67": ("Kozhikode", "Kozhikode", "Kerala"),
    "68": ("Kochi", "Ernakulam", "Kerala"),
    "69": ("Thiruvananthapuram", "Thiruvananthapuram", "Kerala"),
    "70": ("Kolkata", "Kolkata", "West Bengal"),
    "71": ("Howrah", "Howrah", "West Bengal"),
    "72": ("Kharagpur", "Paschim Medinipur", "West Bengal"),
    "73": ("Siliguri", "Darjeeling", "West Bengal"),
    "74": ("Cuttack", "Cuttack", "Odisha"),
    "75": ("Bhubaneswar", "Khurda", "Odisha"),
    "78": ("Guwahati", "Kamrup Metropolitan", "Assam"),
    "79": ("Imphal", "Imphal East", "Manipur"),
    "80": ("Patna", "Patna", "Bihar"),
    "81": ("Bhagalpur", "Bhagalpur", "Bihar"),
    "82": ("Gaya", "Gaya", "Bihar"),
    "83": ("Ranchi", "Ranchi", "Jharkhand"),
    "84": ("Muzaffarpur", "Muzaffarpur", "Bihar"),
    "85": ("Dhanbad", "Dhanbad", "Jharkhand")
}

def lookup_pincode(pincode: str) -> Optional[Dict[str, Any]]:
    """
    Looks up a 6-digit Indian PIN code in the local postal dataset.
    Returns dictionary with city, district, state, post_office, candidate_localities, and match_type.
    """
    clean_pin = str(pincode).strip()
    if not clean_pin or len(clean_pin) != 6 or not clean_pin.isdigit():
        return None

    # 1. Exact PIN Lookup
    if clean_pin in EXACT_PIN_DATABASE:
        data = EXACT_PIN_DATABASE[clean_pin].copy()
        data["pincode"] = clean_pin
        data["match_type"] = "exact_pin_match"
        return data

    # 2. Postal Circle Prefix Lookup (First 2 digits)
    prefix = clean_pin[:2]
    if prefix in POSTAL_PREFIX_MAP:
        city, district, state = POSTAL_PREFIX_MAP[prefix]
        return {
            "pincode": clean_pin,
            "city": city,
            "district": district,
            "state": state,
            "post_office": f"Sub-Office ({clean_pin})",
            "candidate_localities": [city, district],
            "match_type": "postal_circle_prefix_match"
        }

    return None
