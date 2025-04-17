import os
import re
import logging
from dateutil.parser import parse
import requests
from transformers import pipeline
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_huggingface import HuggingFacePipeline

# Load environment variables from .env file
load_dotenv()

HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

# Define headers for both APIs
headers_huggingface = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
}

headers_amadeus = {
    "Authorization": f"Bearer {"KrEwal1skq7D8khGjAAAYyheFewt"}"
}

# Define the flight search function using the Amadeus API
def search_flights(origin, destination, departure_date):
    headers = {"Authorization": f"Bearer {"KrEwal1skq7D8khGjAAAYyheFewt"}"}
    flight_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": 1
    }
    
    response = requests.get(flight_url, headers=headers, params=params)
    
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    
    data = response.json()
    flights = data.get("data", [])
    
    if not flights:
        return f"Sorry, no flights were found from {origin} to {destination} on {departure_date}."

    # Format the output into sentences
    formatted_results = f"Here are some available flights from {origin} to {destination} on {departure_date}:\n\n"
    
    for idx, flight in enumerate(flights[:3], start=1):  # Limiting to 3 flights for readability
        price = flight['price']['total']
        currency = flight['price']['currency']
        departure_info = flight['itineraries'][0]['segments'][0]
        arrival_info = flight['itineraries'][0]['segments'][-1]
        
        departure_time = departure_info['departure']['at']
        arrival_time = arrival_info['arrival']['at']
        airline = departure_info['carrierCode']
        
        formatted_results += (
            f"{idx}. Flight by {airline}: Departs at {departure_time} and arrives at {arrival_time}. "
            f"Total cost: {price} {currency}.\n\n"
        )

    return formatted_results



# Modify the FlightSearchTool class to handle various input formats
class FlightSearchTool(Tool):
    name: str
    description: str
    func: callable

    def __init__(self, name: str = "FlightSearch", description: str = "Search for flights using Amadeus API", func: callable = search_flights):
        super().__init__(name=name, description=description, func=func)

    def _run(self, input_str: str) -> str:
        if 'flight' not in input_str.lower():
            return "Sorry, I can only help with flight searches."

        # Extract origin and destination using regex
        match = re.match(r"flight from (\w+) to (\w+)(.*)", input_str.lower())
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            date_str = match.group(3).strip()

            # Check if there's a date in the input
            date = None
            if date_str:
                try:
                    date = parse(date_str).strftime("%Y-%m-%d")  # Parse and format the date
                except:
                    return "Sorry, I couldn't recognize the date format."

            # Log the details for flight search
            logging.debug(f"Flight search parameters: origin={origin}, destination={destination}, date={date}")

            flights = search_flights(origin.upper(), destination.upper(), date)
            return str(flights)
        else:
            return "Sorry, I couldn't understand the flight details. Please make sure the input is 'flight from <origin> to <destination> [date]'."

# Set up Hugging Face model for conversation generation
conversation_pipeline = pipeline('text-generation', model="microsoft/DialoGPT-medium", max_new_tokens=300, device=1)
llm = HuggingFacePipeline(pipeline=conversation_pipeline)

# Initialize LangChain agent
agent = initialize_agent(
    [FlightSearchTool()],
    llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

# Chat loop for interaction with more flexible input handling
def chat_with_bot():
    print("You can now start chatting with the bot. Type 'exit' to end the conversation.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        logging.debug(f"User Input: {user_input}")

        # Call the FlightSearchTool for debugging
        response = FlightSearchTool()._run(user_input)
        print(f"Chatbot: {response}")

# Start the chat
chat_with_bot()
