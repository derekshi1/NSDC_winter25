import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

AMADEUS_ACCESS_TOKEN = os.getenv("AMADEUS_ACCESS_TOKEN")

if not AMADEUS_ACCESS_TOKEN:
    raise ValueError("Missing Amadeus Access Token. Run get_accesstoken.py first and update your .env file.")

# Test if the access token is valid by hitting the /v1/security/user endpoint
def test_access_token():
    url = "https://test.api.amadeus.com/v1/security/user"
    headers = {
        "Authorization": f"Bearer {AMADEUS_ACCESS_TOKEN}",
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("Access token is valid!")
        return True
    else:
        print(f"Access token is invalid: {response.status_code} - {response.text}")
        return False

# Run the test
if test_access_token():
    print("Token is valid. Proceeding with hotel offers.")
else:
    print("Token validation failed. Please regenerate your access token.")