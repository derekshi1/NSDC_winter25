import os
from dotenv import load_dotenv
load_dotenv()

print("API Key:", os.getenv("AMADEUS_API_KEY"))
print("API Secret:", os.getenv("AMADEUS_API_SECRET"))