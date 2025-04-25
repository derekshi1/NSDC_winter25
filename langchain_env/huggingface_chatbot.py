import requests
import os
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from datetime import datetime, timedelta
import torch

# Load environment variables from .env
load_dotenv()

# Load RapidAPI Key
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Load Hugging Face Chatbot
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
tokenizer.pad_token = tokenizer.eos_token  # Set pad token to eos token for compatibility
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

# Function to generate a chatbot response
def generate_chatbot_response(user_input):
    inputs = tokenizer(user_input + tokenizer.eos_token, return_tensors='pt', padding=True)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    chat_history_ids = model.generate(
        input_ids,
        attention_mask=attention_mask,
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id,
        top_p=0.95,
        top_k=60,
        do_sample=True
    )

    chatbot_response = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
    return chatbot_response

# Function to fetch hotels using Travel Advisor API
def fetch_hotel_offers(city_name):
    url = "https://travel-advisor.p.rapidapi.com/locations/search"
    querystring = {
        "query": city_name,
        "limit": "1",
        "offset": "0",
        "units": "km",
        "location_id": "1",
        "currency": "USD",
        "sort": "relevance",
        "lang": "en_US"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
    }

    # Step 1: Get location_id for the city
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        return f"Error fetching city data: {response.status_code} - {response.text}"
    
    data = response.json()
    try:
        location_id = data["data"][0]["result_object"]["location_id"]
    except (KeyError, IndexError):
        return f"Could not find hotels for '{city_name}'."

    # Step 2: Get hotels for that location_id
    checkin_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')  # Default to tomorrow
    hotel_url = "https://travel-advisor.p.rapidapi.com/hotels/list"
    hotel_query = {
        "location_id": location_id,
        "checkin": checkin_date,
        "adults": "1",
        "rooms": "1",
        "nights": "1",
        "currency": "USD",
        "order": "asc",
        "limit": "5",
        "lang": "en_US"
    }

    hotel_response = requests.get(hotel_url, headers=headers, params=hotel_query)
    if hotel_response.status_code != 200:
        return f"Error fetching hotel data: {hotel_response.status_code} - {hotel_response.text}"

    hotels_data = hotel_response.json()
    hotel_names = [hotel.get("name") for hotel in hotels_data.get("data", []) if hotel.get("name")]

    return hotel_names if hotel_names else f"No hotels found for '{city_name}'."

# Chatbot interaction
def chatbot_with_hotel_info():
    print("Hello! I'm your travel assistant chatbot. Ask me about hotels. Say 'exit' to quit.")

    while True:
        user_input = input("You: ").strip().lower()
        if user_input in ["exit"]:
            print("Safe travels! Let me know if you need help in the future.")
            break

        if "hotel" in user_input and "in" in user_input:
            city_name = user_input.split("in")[-1].strip()
            hotel_data = fetch_hotel_offers(city_name)

            if isinstance(hotel_data, list):
                print(f"Found hotels in {city_name.title()}: {', '.join(hotel_data)}")
            else:
                print(hotel_data)
        else:
            chatbot_response = generate_chatbot_response(user_input)
            print("Chatbot:", chatbot_response)

def test_location_search(city="paris"):
    url = "https://travel-advisor.p.rapidapi.com/locations/search"
    querystring = {
        "query": city,
        "limit": "1",
        "offset": "0",
        "units": "km",
        "currency": "USD",
        "sort": "relevance",
        "lang": "en_US"
    }
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    print("Status code:", response.status_code)
    print("Response JSON:", response.json())

def test_hotels_list(location_id="293928"):  # Cancun, known to return hotels
    from datetime import datetime, timedelta
    checkin_date = (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d')  # Give it breathing room

    url = "https://travel-advisor.p.rapidapi.com/hotels/list"
    params = {
        "location_id": location_id,
        "checkin": checkin_date,
        "adults": "1",
        "rooms": "1",
        "nights": "3",
        "currency": "USD",
        "order": "asc",
        "limit": "10",
        "lang": "en_US"
    }

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=params)
    print("Status code:", response.status_code)
    data = response.json()
    hotel_names = [hotel.get("name") for hotel in data.get("data", []) if hotel.get("name")]
    print("Hotels Found:", hotel_names if hotel_names else "No hotels returned.")

# Run chatbot
if __name__ == "__main__":
    test_hotels_list("293928")  # Test with Cancun location_id
    # chatbot_with_hotel_info()