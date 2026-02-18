import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")

# Free API endpoint
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def chat_with_free_api(messages, model="openrouter/free", max_tokens=1000, temperature=0.7):
    """
    Send a chat request to the Free API

    Args:
        messages (list): List of message objects with 'role' and 'content'
        model (str): Model to use (default: openrouter/free)
        max_tokens (int): Maximum tokens in response (default: 1000)
        temperature (float): Temperature for response generation (default: 0.7)

    Returns:
        dict: Response from the API
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": os.getenv("HTTP_REFERER", "http://localhost:5000"),
        "X-Title": os.getenv("APP_TITLE", "Free API Test"),
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": True,
            "status_code": response.status_code,
            "message": response.text
        }

def main():
    # Example 1: Simple chat
    print("Example 1: Simple chat")
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    response = chat_with_free_api(messages)
    if not response.get("error"):
        print(response['choices'][0]['message']['content'])
        print(f"Model used: {response.get('model', 'N/A')}")
    else:
        print(f"Error: {response}")

    print("
" + "="*50 + "
")

    # Example 2: Multi-turn conversation
    print("Example 2: Multi-turn conversation")
    conversation = [
        {"role": "user", "content": "I'm learning Python. Can you help me?"},
        {"role": "assistant", "content": "Of course! I'd be happy to help you learn Python. What specific topic would you like to start with?"},
        {"role": "user", "content": "How do I create a list in Python?"}
    ]
    response = chat_with_free_api(conversation)
    if not response.get("error"):
        print(response['choices'][0]['message']['content'])
    else:
        print(f"Error: {response}")

    print("
" + "="*50 + "
")

    # Example 3: System message
    print("Example 3: System message")
    messages = [
        {"role": "system", "content": "You are a helpful assistant that specializes in programming."},
        {"role": "user", "content": "What's the difference between a list and a tuple in Python?"}
    ]
    response = chat_with_free_api(messages)
    if not response.get("error"):
        print(response['choices'][0]['message']['content'])
    else:
        print(f"Error: {response}")

if __name__ == "__main__":
    main()
