from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import time
from datetime import datetime, timedelta

# Load Hugging Face Chatbot
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

# Function to generate chatbot response
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

# Updated: Find hotels using Selenium

def find_hotels(city):
    print(f"Searching hotels in {city.title()} using Selenium on Booking.com...")

    options = Options()
    # options.add_argument("--headless")  # Uncomment for production use
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service("C:/chromedriver/chromedriver.exe/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    checkin = datetime.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)
    checkin_str = checkin.strftime('%Y-%m-%d')
    checkout_str = checkout.strftime('%Y-%m-%d')

    city_query = city.replace(" ", "+")
    url = f"https://www.booking.com/searchresults.html?ss={city_query}&checkin={checkin_str}&checkout={checkout_str}&rows=10"
    driver.get(url)

    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="property-card"]')))

    hotels = []
    hotel_cards = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="property-card"]')

    for card in hotel_cards:
        try:
            name = card.find_element(By.CSS_SELECTOR, 'div[data-testid="title"]').text
        except:
            name = "Unnamed Hotel"

        try:
            rating = card.find_element(By.CSS_SELECTOR, 'div[data-testid="review-score"] > div:nth-child(1)').text
        except:
            rating = "No rating"

        try:
            price = card.find_element(By.CSS_SELECTOR, 'span[data-testid="price-and-discounted-price"]').text
        except:
            try:
                price = card.find_element(By.CSS_SELECTOR, 'div[data-testid="price-and-discounted-price"]').text
            except:
                try:
                    price = card.find_element(By.CSS_SELECTOR, 'span[class*="fcab3ed991"]').text
                except:
                    price = "No price"

        hotels.append((name, rating, price))

    driver.quit()
    return hotels if hotels else ["No hotels found."]

# Chatbot interaction
def chatbot():
    print("Hello! I'm your travel assistant chatbot. Ask me about hotels. Say 'exit' to quit.")

    while True:
        user_input = input("You: ").strip().lower()
        if user_input in ["exit", "quit", "bye"]:
            print("Safe travels! Let me know if you need help in the future.")
            break

        if "hotel" in user_input and "in" in user_input:
            city_name = user_input.split("in")[-1].strip()

            sort_by = None
            if any(keyword in user_input for keyword in ["cheap", "lowest", "price"]):
                sort_by = "price"
            elif any(keyword in user_input for keyword in ["top rated", "best rated", "highest", "rating"]):
                sort_by = "rating"

            hotel_data = find_hotels(city_name)

            def extract_price(hotel):
                for part in hotel:
                    if "$" in part:
                        try:
                            return float(part.replace("$", "").replace(",", "").strip())
                        except:
                            return float("inf")
                return float("inf")

            def extract_rating(hotel):
                try:
                    return float(hotel[1].strip())
                except:
                    return 0.0

            if isinstance(hotel_data, list) and isinstance(hotel_data[0], tuple):
                if sort_by == "price":
                    hotel_data.sort(key=extract_price)
                elif sort_by == "rating":
                    hotel_data.sort(key=extract_rating, reverse=True)

                hotel_data = hotel_data[:5]  # Limit to top 5
                print(f"\nTop Hotels in {city_name.title()}\n{'='*40}")
                for name, rating, price in hotel_data:
                    print(f"🏨 {name}\n   ⭐ Rating: {rating} | 💲Price: {price}\n")
            else:
                print(hotel_data)

        else:
            chatbot_response = generate_chatbot_response(user_input)
            print("Chatbot:", chatbot_response)

# Run the chatbot
if __name__ == "__main__":
    chatbot()
