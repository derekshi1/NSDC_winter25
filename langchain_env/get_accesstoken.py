import requests

# Your Amadeus credentials
client_id = "k6ewkyIXrQrl7y6hmyOziMAkaH5IX1aU"  # Replace with your actual API key
client_secret = "Ex3HVnjikoGxqVXJ"  # Replace with your actual API secret

# Request body
data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret
}

# Send the POST request to get the access token
response = requests.post("https://test.api.amadeus.com/v1/security/oauth2/token", data=data)

# Check if the request was successful
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    token_expiry = token_data["expires_in"]  # The expiration time in seconds from now

    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
    print(f"Token Expiry Time (in seconds): {token_expiry}")
else:
    print(f"Error: {response.status_code} - {response.text}")