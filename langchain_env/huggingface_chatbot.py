import requests
import os
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load environment variables from .env
load_dotenv()

AMADEUS_ACCESS_TOKEN = os.getenv("AMADEUS_ACCESS_TOKEN")
if not AMADEUS_ACCESS_TOKEN:
    raise ValueError("Missing Amadeus Access Token. Run get_accesstoken.py first and update your .env file.")

# Function to fetch hotel offers
def fetch_hotel_offers(city_code):
    url = "https://test.api.amadeus.com/v2/shopping/hotel-offers"
    headers = {
        "Authorization": f"Bearer {AMADEUS_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "cityCode": city_code
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return f"Error fetching hotel data: {response.status_code} - {response.text}"

# Load Hugging Face Chatbot
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

# Function to generate a chatbot response
def generate_chatbot_response(user_input):
    new_user_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')

    bot_input_ids = new_user_input_ids
    chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id, top_p=0.95, top_k=60, do_sample=True)

    chatbot_response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

    return chatbot_response

# Function to handle interaction
def chatbot_with_hotel_info():
    print("Hello! I'm your travel assistant chatbot. Ask me about hotels.")
    
    while True:
        user_input = input("You: ")
        
        if "hotel" in user_input.lower() and "in" in user_input.lower():
            city_code = user_input.split("in")[-1].strip()
            hotel_data = fetch_hotel_offers(city_code)
            
            if isinstance(hotel_data, dict):  # Check if we received valid hotel data
                hotels = [offer['hotel']['name'] for offer in hotel_data.get('data', [])]
                if hotels:
                    print(f"Found hotels in {city_code}: {', '.join(hotels)}")
                else:
                    print(f"No hotels found in {city_code}.")
            else:
                print(hotel_data)  # Display error if hotel data isn't retrieved correctly

        else:
            chatbot_response = generate_chatbot_response(user_input)
            print("Chatbot:", chatbot_response)

# Run chatbot with Amadeus API integration
if __name__ == "__main__":
    chatbot_with_hotel_info()