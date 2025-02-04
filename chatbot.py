import os
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
load_dotenv()

OPEN_AI_API_KEY = os.getenv("API_KEY")
# Initialize OpenAI chat model
chat_model = ChatOpenAI(api_key=OPEN_AI_API_KEY, model="gpt-4o-mini")
# Chat history
chat_history = [
    SystemMessage(content="You are a helpful AI assistant."),
]

# Chatbot loop
print("🤖 LangChain Chatbot is running! Type 'exit' to stop.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Chatbot: Goodbye! 👋")
        break

    # Add user message to history
    chat_history.append(HumanMessage(content=user_input))

    # Get AI response
    response = chat_model(chat_history)

    # Add AI message to history
    chat_history.append(AIMessage(content=response.content))

    # Print AI response
    print(f"Chatbot: {response.content}\n")
