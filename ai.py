from openai import OpenAI
from config import OPENAI_API_KEY

# Initialize client only if API key is provided to prevent startup crash
client = None
if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")

SYSTEM_PROMPT = """
You are Jarvis, an advanced AI voice assistant created for Arjun.

Speak like a personal AI: friendly, natural, and keep short.
Help with coding, productivity, and learning.
If user asks to continue, keep the conversation going.
"""

chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


def ask_ai(prompt: str) -> str:
    chat_history.append({"role": "user", "content": prompt})

    # Local QA offline fallback
    cleaned_prompt = prompt.lower().strip().replace("?", "").replace(".", "")
    local_qa = {
        "what is python": "Arjun, Python is a popular, high-level programming language created by Guido van Rossum and released in 1991. It is widely used for web development, data science, artificial intelligence, and scripting.",
        "who is the father of python": "Arjun, the father of Python is Guido van Rossum, a Dutch programmer who designed and created the language in the late 1980s.",
        "who created python": "Arjun, Python was created by Guido van Rossum in the late 1980s.",
        "creator of python": "Arjun, Python was created by Guido van Rossum.",
        "who are you": "Arjun, I am Chinni, your personal AI assistant.",
        "what is your name": "Arjun, my name is Chinni, your custom AI OS assistant."
    }
    
    for question, answer in local_qa.items():
        if question in cleaned_prompt:
            reply = answer
            chat_history.append({"role": "assistant", "content": reply})
            return reply

    try:
        if not client:
            raise ValueError("OpenAI API key is missing or empty.")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_history
        )

        reply = response.choices[0].message.content
    except Exception:
        # Keep the conversation alive even when the OpenAI API fails
        # (e.g., rate limit, invalid key, insufficient quota).
        reply = "Arjun, I’m having trouble connecting to my AI right now. Please try again." 
        chat_history.append({
            "role": "assistant",
            "content": reply
        })
        return reply

    chat_history.append({
        "role": "assistant",
        "content": reply
    })

    return reply



