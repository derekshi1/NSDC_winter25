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

# ——— HuggingFace DialoGPT setup (unchanged) ———
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
tokenizer.pad_token = tokenizer.eos_token
model     = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

def generate_chatbot_response(user_input: str) -> str:
    inputs         = tokenizer(user_input + tokenizer.eos_token, return_tensors='pt', padding=True)
    chat_ids       = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id,
        top_p=0.95, top_k=60, do_sample=True
    )
    return tokenizer.decode(
        chat_ids[:, inputs.input_ids.shape[-1]:][0],
        skip_special_tokens=True
    )

# ——— Updated find_hotels to accept dates & nights ———
def find_hotels(city_name: str, checkin_date: datetime, nights: int):
    checkout_date = checkin_date + timedelta(days=nights)
    checkin_str   = checkin_date.strftime("%Y-%m-%d")
    checkout_str  = checkout_date.strftime("%Y-%m-%d")

    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    city_query = city_name.replace(" ", "+")
    url = (
        "https://www.booking.com/searchresults.html"
        f"?ss={city_query}"
        f"&checkin={checkin_str}"
        f"&checkout={checkout_str}"
        "&rows=10"
    )
    driver.get(url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="property-card"]'))
    )

    hotels      = []
    hotel_cards = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="property-card"]')
    for card in hotel_cards:
        # name
        try:
            name = card.find_element(By.CSS_SELECTOR, 'div[data-testid="title"]').text
        except:
            name = "Unnamed Hotel"
        # rating
        try:
            rating = card.find_element(
                By.CSS_SELECTOR, 'div[data-testid="review-score"] > div:nth-child(1)'
            ).text
        except:
            rating = "No rating"
        # total price
        try:
            price = card.find_element(
                By.CSS_SELECTOR, 'span[data-testid="price-and-discounted-price"]'
            ).text
        except:
            price = "0"
        # compute numeric values
        total_price = float(price.replace("$","").replace(",","")) if "$" in price else 0.0
        per_night   = total_price / nights if nights else 0.0

        hotels.append({
            "Name": name,
            "Rating": rating,
            "Total Price": f"${total_price:,.2f}",
            "Price per Night": f"${per_night:,.2f}"
        })

    driver.quit()
    return hotels

# ——— Streamlit App ———
st.set_page_config(page_title="🏨 Travel Dashboard", layout="wide")
st.title("🏖 Travel Assistant Dashboard")

# Persist state
if "last_city"     not in st.session_state: st.session_state["last_city"] = ""
if "last_checkin"  not in st.session_state: st.session_state["last_checkin"] = datetime.today()
if "last_nights"   not in st.session_state: st.session_state["last_nights"] = 2
if "last_hotels"   not in st.session_state: st.session_state["last_hotels"] = []
if "chat_history"  not in st.session_state: st.session_state["chat_history"] = []

# — Search Panel —
st.header("Search Hotels")
city        = st.text_input("City", value=st.session_state["last_city"])
checkin     = st.date_input("Check‑in Date", value=st.session_state["last_checkin"])
nights      = st.number_input("Number of Nights", min_value=1, value=st.session_state["last_nights"])

# Buttons in row 1
col1, col2 = st.columns(2)
with col1:
    if st.button("🔎 Search"):
        st.session_state["last_city"]     = city
        st.session_state["last_checkin"]  = checkin
        st.session_state["last_nights"]   = nights
        # fetch and store
        st.session_state["last_hotels"]   = find_hotels(city, datetime.combine(checkin, datetime.min.time()), nights)
with col2:
    if st.button("💲 Cheapest") and st.session_state["last_hotels"]:
        st.session_state["last_hotels"].sort(
            key=lambda h: float(h["Total Price"].replace("$","").replace(",",""))
        )

# Buttons in row 2
col3, col4 = st.columns(2)
with col3:
    if st.button("⭐ Top Rated") and st.session_state["last_hotels"]:
        st.session_state["last_hotels"].sort(
            key=lambda h: float(h["Rating"]) if h["Rating"]!="No rating" else 0.0,
            reverse=True
        )
with col4:
    # blank or other controls…
    pass

# Results Table
if st.session_state["last_hotels"]:
    st.subheader(
        f"Results for {st.session_state['last_city'].title()} — "
        f"{st.session_state['last_checkin'].strftime('%Y/%m/%d')} for {st.session_state['last_nights']} nights"
    )
    st.table(st.session_state["last_hotels"][:5])

st.markdown("---")

# — Chat Panel (fallback) —
st.header("General Chat")
user_msg = st.text_input("You:", key="user_input")
if st.button("Send") and user_msg:
    st.session_state["chat_history"].append(("You", user_msg))
    # if they mention hotels, show ack
    if "hotel" in user_msg.lower() and "in" in user_msg.lower():
        st.session_state["chat_history"].append(
            ("Bot", f"Searching hotels in {st.session_state['last_city'].title()}…")
        )
    else:
        reply = generate_chatbot_response(user_msg)
        st.session_state["chat_history"].append(("Bot", reply))
    st.session_state["user_input"] = ""

# Render chat
for speaker, text in st.session_state["chat_history"]:
    if speaker == "You":
        st.markdown(f"**You:** {text}")
    else:
        st.markdown(f"**Bot:** {text}")
