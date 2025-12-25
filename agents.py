import os

# Custom endpoint with minimal response
from typing import Optional

import requests
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from dotenv import load_dotenv
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader

load_dotenv()  # Load environment variables including OPENAI_API_KEY

# Read resume from PDF
reader = PdfReader("me/Harish_Frontend_Resume.pdf")
resume = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        resume += text

name = "Harish"

# Create system prompt with lead collection instructions
system_prompt = f"""
You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer, say so.

IMPORTANT - LEAD COLLECTION:
When users show interest in working with {name}, wanting to discuss a project, or requesting a meeting/consultation, \
you MUST collect their contact information:
1. Name
2. Email address
3. Subject (what they want to discuss)
4. Preferred date for the meeting
5. Preferred time slot in IST (Indian Standard Time)

LEAD COLLECTION GUIDELINES:
- Users may provide all information in one message (e.g., "I'm John, john@example.com, want to discuss web development, Tuesday Jan 15th, 3 PM IST") - extract and use the send_lead_to_telegram tool immediately
- If they don't provide all details, ask for missing information conversationally and naturally
- Ask in this order: name, email, subject/topic, preferred date, then time slot
- Once you have all five pieces of information (name, email, subject, date, and time slot in IST), IMMEDIATELY use the send_lead_to_telegram tool
- After successfully sending the lead, thank them and let them know {name} will reach out soon
- Be natural and conversational while collecting this information

"""

system_prompt += f"""\n\nbackground:{resume}\n\n"""

system_prompt += f"""
With this context, please chat with the user, always staying in character as {name}.
"""


# Tool function to send lead information to Telegram
def send_lead_to_telegram(
    name: str, email: str, subject: str, date: str, time_slot_ist: str
) -> str:
    """
    Send lead information to Telegram.

    Args:
        name: The name of the lead
        email: The email address of the lead
        subject: What the lead wants to discuss
        date: The preferred date for the meeting
        time_slot_ist: The preferred time slot in IST (Indian Standard Time)

    Returns:
        Success or error message
    """
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not telegram_bot_token or not telegram_chat_id:
        return "Error: Telegram credentials not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file"

    # Format the message
    message = f"""
🆕 New Lead from Website!

👤 Name: {name}
📧 Email: {email}
📝 Subject: {subject}
📅 Preferred Date: {date}
🕐 Preferred Time (IST): {time_slot_ist}

---
Please reach out to them soon!
"""

    # Send message to Telegram
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        if response.json().get("ok"):
            return f"Successfully sent lead information for {name} to Telegram! I'll make sure to reach out to you soon."
        else:
            return f"Error sending to Telegram: {response.json().get('description', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return f"Error sending to Telegram: {str(e)}"


# Create Agno agent with memory, session management, and tools
# Uses OPENAI_API_KEY from environment variables
agno_agent = Agent(
    name=f"{name} Chatbot Agent",
    model=OpenAIChat(id="gpt-4o"),  # Using OpenAI GPT-4o model
    db=SqliteDb(db_file="agno.db"),  # SQLite database for session persistence
    instructions=system_prompt,
    tools=[send_lead_to_telegram],  # Add the Telegram tool
    add_history_to_context=True,  # Enable conversation history
    markdown=True,
    description=f"A chatbot representing {name}, answering questions about career, background, skills and experience, and collecting leads",
)

# Create AgentOS and get FastAPI app
agent_os = AgentOS(agents=[agno_agent])
app = agent_os.get_app()

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (use specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.post("/chat")
async def chat_endpoint(
    message: str = Form(...), session_id: Optional[str] = Form(None)
):
    """
    Simplified chat endpoint that returns only essential fields.
    """
    # Run the agent
    response = agno_agent.run(message, session_id=session_id)

    # Return only minimal fields
    return {
        "run_id": response.run_id,
        "agent_id": response.agent_id,
        "agent_name": agno_agent.name,
        "session_id": response.session_id,
        "content": response.content,
    }


# Chat interface (for testing via CLI)
def chat():
    print(f"=== Chat with {name} ===")
    print("Type 'quit' or 'exit' to end the conversation\n")

    session_id = "cli_session"  # Session ID for CLI testing

    while True:
        # Get user input
        user_input = input("You: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Use agent.run with session_id for memory persistence
            response = agno_agent.run(user_input, session_id=session_id)

            # Display response
            print(f"\n{name}: {response.content}\n")

        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    import sys

    # If running with CLI, use the chat interface
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        chat()
    else:
        # Otherwise, run the FastAPI server
        import uvicorn

        print(f"Starting {name} Chatbot API server...")
        print("API available at: http://localhost:8000")
        print("API docs at: http://localhost:8000/docs")
        print("Run with 'python agents.py chat' for CLI mode")
        print(
            "\nMake sure to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file!"
        )
        uvicorn.run(app, host="0.0.0.0", port=8000)
