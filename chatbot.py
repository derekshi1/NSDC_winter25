from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

OPEN_AI_API_KEY = "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"

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
