import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Amadeus API credentials and refresh token
api_key = os.getenv("AMADEUS_API_KEY")
api_secret = os.getenv("AMADEUS_API_SECRET")
refresh_token = os.getenv("AMADEUS_REFRESH_TOKEN")

# Define the endpoint for token refresh
token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
data = {
    "grant_type": "refresh_token",
    "client_id": api_key,
    "client_secret": api_secret,
    "refresh_token": refresh_token
}

# Request the new access token using the refresh token
response = requests.post(token_url, data=data)

# Check if the request was successful
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data["expires_in"]
    
    # Save the new tokens to your .env file
    with open(".env", "a") as env_file:
        env_file.write(f"\nAMADEUS_ACCESS_TOKEN={access_token}")
        env_file.write(f"\nAMADEUS_REFRESH_TOKEN={refresh_token}")
        env_file.write(f"\nAMADEUS_TOKEN_EXPIRY={expires_in}")
    
    print(f"New Access Token: {access_token}")
    print(f"New Refresh Token: {refresh_token}")
else:
    print(f"Error refreshing token: {response.status_code} - {response.text}")