import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from transformers import AutoModelForCausalLM, AutoTokenizer
from datetime import datetime, timedelta
from webdriver_manager.chrome import ChromeDriverManager

# Load Hugging Face Chatbot
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

# Function to generate chatbot response
def generate_chatbot_response(user_input: str) -> str:
    inputs = tokenizer(user_input + tokenizer.eos_token, return_tensors='pt', padding=True)
    chat_ids = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id,
        top_p=0.95,
        top_k=60,
        do_sample=True
    )
    # decode only new tokens
    return tokenizer.decode(
        chat_ids[:, inputs.input_ids.shape[-1]:][0],
        skip_special_tokens=True
    )

# Updated: Find hotels using Selenium

def find_hotels(city):
    print(f"Searching hotels in {city.title()} using Selenium on Booking.com...")

    options = Options()
    #options.add_argument("--headless")  # Uncomment for production use
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    checkin = datetime.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)
    checkin_str = checkin.strftime('%Y-%m-%d')
    checkout_str = checkout.strftime('%Y-%m-%d')

    # Construct search URL with 10 rows
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

#def of functions to get prices
def extract_price(hotel):
    try:
        return float(hotel[2].replace('$', '').replace(',', ''))
    except:
        return float('inf')


def extract_rating(hotel):
    try:
        return float(hotel[1])
    except:
        return 0.0
    


# Streamlit app setup
st.set_page_config(page_title="🏨 Travel Dashboard", layout="wide")
st.title("🏖 Travel Assistant Dashboard")

#Initialize session state for follow-up logic and chat history
if "last_city" not in st.session_state:
    st.session_state["last_city"] = ""
if "last_hotels" not in st.session_state:
    st.session_state["last_hotels"] = []
if "chat" not in st.session_state:
    st.session_state["chat"] = []

#streamlit hotel search
st.header("Search Hotels")
city = st.text_input("Enter city name", value=st.session_state["last_city"])
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔎 Search"):
        # New: Run scraper and store in session_state
        st.session_state["last_city"] = city
        st.session_state["last_hotels"] = find_hotels(city)
with col2:
    if st.button("💲 Cheapest") and st.session_state["last_hotels"]:
        # New: Sort in-place by price
        st.session_state["last_hotels"].sort(key=extract_price)
with col3:
    if st.button("⭐ Top Rated") and st.session_state["last_hotels"]:
        # New: Sort in-place by rating
        st.session_state["last_hotels"].sort(key=extract_rating, reverse=True)

# New: Display table of top 5 hotels
if st.session_state["last_hotels"]:
    st.subheader(f"Results for {st.session_state['last_city'].title()}")
    st.table(st.session_state["last_hotels"][:5])

st.markdown("---")
#Chatbot Panel—————————————————————————————————————————
st.header("General Chat")
user_msg = st.text_input("You:", key="user_input")
if st.button("Send") and user_msg:
    # Determine if user is asking about hotels or general chat
    u = user_msg.lower()
    if "hotel" in u and "in" in u:
        # New: mimic search acknowledgement
        st.session_state["chat"].append(("You", user_msg))
        st.session_state["chat"].append(("Bot", f"Searching hotels in {st.session_state['last_city'].title()}…"))
    else:
        # Existing: fallback to DialoGPT reply
        reply = generate_chatbot_response(user_msg)
        st.session_state["chat"].append(("You", user_msg))
        st.session_state["chat"].append(("Bot", reply))
    # Clear input box
    st.session_state["user_input"] = ""

# New: Render chat history below
for speaker, text in st.session_state["chat"]:
    if speaker == "You":
        st.markdown(f"**You:** {text}")
    else:
        st.markdown(f"**Bot:** {text}")