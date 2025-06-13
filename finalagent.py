from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor, tool
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from langchain_tavily import TavilySearch
from notion_client import Client
from langchain.memory import ConversationBufferMemory

import logging
import json
import time
import random
from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory
from playwright.sync_api import sync_playwright

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()
from langchain.agents import tool


PROJECT_ID = "langchain-ad165"
SESSION_ID = "user_session_new"  # This can be username or unique ID
COLLECTION_NAME = "chat_history"

client = firestore.Client(project=PROJECT_ID)

chat_history=FirestoreChatMessageHistory(
    session_id=SESSION_ID,
    collection=COLLECTION_NAME,
    client=client,

)

with open("config.json", "r") as f:
    config = json.load(f)

def human_sleep(min_time=0.8, max_time=2.5):
    time.sleep(random.uniform(min_time, max_time))
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Tavily search with better configuration
tavily_search_tool = TavilySearch(
    max_results=3,  # Reduced for better performance
    topic='general',
    include_answer=True,
    include_raw_content=False  # Avoid overwhelming the agent
)

# Improved prompt template that's less restrictive
my_prompt_template = PromptTemplate(
    input_variables=["input", "agent_scratchpad", "chat_history"],
    template="""
You are a helpful AI assistant with access to tools.

Conversation so far:
{chat_history}

Use the following tools to help answer questions:
- get_system_time: Get current date/time
- tavily_search: Search the web for current information
- llm_query: Get general knowledge answers
- research_and_analyze: Combine web search with analysis for comprehensive answers
- apply_linkedin_jobs: Automates applying to LinkedIn jobs using config.json and Playwright.

Think step by step and use tools when needed.

{agent_scratchpad}

Question: {input}
"""
)
def click_next_or_submit(page):
    try:
        next_btn = page.query_selector('button[aria-label*="Next"]')
        if next_btn:
            next_btn.click()
            print(" Clicked Next. ")
            return "next"

        submit_btn = page.query_selector('button[aria-label*="Submit application"]')
        if submit_btn:
            submit_btn.click()
            print(" Application submitted !!")
            return "submit"

        print(" No Next or Submit button.")
        return "done"
    except Exception as e:
        print(f"❌ Error clicking next or submit: {e}")
        return "error"


memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    chat_memory=chat_history
)

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from notion_client import Client

@tool
def generate_and_append_note_to_notion(topic: str) -> str:
    """
    Generates AI-written notes on a topic and appends them to a Notion page.
    
    Example:
    Input: Arduino
    Output: Creates notes about Arduino and adds them to Notion.
    """
    try:
        NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        PAGE_ID = os.getenv("NOTION_PAGE_ID")

        if not NOTION_TOKEN or not PAGE_ID:
            return "❌ Error: Missing NOTION_TOKEN or NOTION_PAGE_ID in environment variables."

        # Step 1: Generate notes using LLM
        prompt = f"Write detailed, structured study notes on the topic: {topic}. Use bullet points or sections if helpful."
        notes = llm.invoke(prompt)
        notes_text = notes.content if hasattr(notes, 'content') else str(notes)

        # Step 2: Append to Notion
        notion = Client(auth=NOTION_TOKEN)

        notion.blocks.children.append(
            block_id=PAGE_ID,
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": f"Notes on {topic}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": notes_text}}]
                    }
                }
            ]
        )

        return f"✅ Notes on '{topic}' added to Notion."

    except Exception as e:
        return f"❌ Failed to generate and append notes: {e}"


@tool
def append_to_notion_page(text: str) -> str:
    """
    Appends a paragraph block to a Notion page.
    Input should be plain text. The page must be shared with the integration.
    
    Example:
    Add Summary of today's AI meeting and plans for tomorrow.
    """

    try:
        NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        PAGE_ID = os.getenv("NOTION_PAGE_ID")  # No dashes or with dashes both work

        if not NOTION_TOKEN or not PAGE_ID:
            return "❌ Error: NOTION_TOKEN or NOTION_PAGE_ID is missing in environment variables."

        notion = Client(auth=NOTION_TOKEN)

        notion.blocks.children.append(
            block_id=PAGE_ID,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": text
                                }
                            }
                        ]
                    }
                }
            ]
        )

        return "✅ Successfully appended text to Notion page."

    except Exception as e:
        return f"❌ Failed to append to Notion page: {e}"

@tool
def create_calendar_event(details: str) -> str:
    """
    Creates a Google Calendar event.
    Expects structured input:
    Title: Meeting with Team
    Date: 2025-06-15
    Time: 14:00
    Duration: 1  # in hours
    Description: Discussion on project milestones
    """

    try:
        # Parse input
        lines = details.strip().split("\n")
        event = {
            "summary": "",
            "description": "",
            "start": {},
            "end": {},
        }

        for line in lines:
            if "Title:" in line:
                event["summary"] = line.split("Title:")[1].strip()
            elif "Date:" in line:
                date = line.split("Date:")[1].strip()
            elif "Time:" in line:
                time_ = line.split("Time:")[1].strip()
            elif "Duration:" in line:
                duration = int(line.split("Duration:")[1].strip())
            elif "Description:" in line:
                event["description"] = line.split("Description:")[1].strip()

        start_datetime = f"{date}T{time_}:00"
        end_hour = int(time_.split(":")[0]) + duration
        end_datetime = f"{date}T{end_hour:02d}:{time_.split(':')[1]}:00"

        event["start"]["dateTime"] = start_datetime
        event["start"]["timeZone"] = "Asia/Kolkata"
        event["end"]["dateTime"] = end_datetime
        event["end"]["timeZone"] = "Asia/Kolkata"

        # Auth
        scopes = ["https://www.googleapis.com/auth/calendar"]
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
        creds = flow.run_local_server(port=3000)
        service = build("calendar", "v3", credentials=creds)

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Event created: {created_event.get('htmlLink')}"

    except Exception as e:
        return f"❌ Failed to create event: {e}"



@tool
def write_email(email_text: str) -> str:
    """
    Sends an email. Expects structured input:
    To: recipient@example.com
    Subject: Your subject here
    Body:
    The body of the email goes here.
    """

    try:
        # Split and parse input
        lines = email_text.strip().split("\n")
        to = next((line.split("To:")[1].strip() for line in lines if line.startswith("To:")), None)
        subject = next((line.split("Subject:")[1].strip() for line in lines if line.startswith("Subject:")), None)
        
        body_index = next((i for i, line in enumerate(lines) if line.strip() == "Body:"), None)
        body = "\n".join(lines[body_index+1:]).strip() if body_index is not None else None

        if not to or not subject or not body:
            return "❌ Error: Email must include 'To:', 'Subject:', and 'Body:'."

        # Credentials
        sender_email = os.getenv("GMAIL_ADDRESS")
        app_password = os.getenv("GMAIL_APP_PASSWORD")

        if not sender_email or not app_password:
            return "❌ Missing Gmail credentials in environment variables."

        # Compose email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to, msg.as_string())

        return f"✅ Email successfully sent to {to}."

    except Exception as e:
        return f"❌ Failed to send email: {e}"

@tool
def apply_linkedin_jobs(_: str = "") -> str:
    """Applies to LinkedIn jobs using stored config.json and Playwright automation."""
    logs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.get("headless", False))
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://www.linkedin.com/login")
            human_sleep()
            page.fill('input[name="session_key"]', config["email"])
            human_sleep()
            page.fill('input[name="session_password"]', config["password"])
            human_sleep()
            page.click('button[type="submit"]')
            human_sleep()
            page.wait_for_selector('a.global-nav__primary-link--active', timeout=0)
            logs.append("✅ Login successful.")

            page.goto("https://www.linkedin.com/jobs/")
            time.sleep(3)
            search_box = page.get_by_role("combobox", name="Search by title, skill, or")
            search_box.click()
            time.sleep(3)
            search_box.fill(config["search_term"])
            search_box.press("Enter")
            time.sleep(5)
            page.click("//button[@aria-label='Easy Apply filter.']")
            logs.append("🎯 Job search & filter applied.")

            current_page = 1
            job_counter = 0
            max_pages = config.get("max_pages", 5)

            while current_page <= max_pages:
                logs.append(f"📄 Page {current_page}")
                job_listings = page.query_selector_all('//div[contains(@class,"display-flex job-card-container")]')

                if not job_listings:
                    logs.append("No jobs found.")
                    break

                for job in job_listings:
                    try:
                        job_counter += 1
                        logs.append(f"➡️ Job {job_counter}")
                        job.click()
                        time.sleep(2)

                        if page.query_selector('span.artdeco-inline-feedback__message:has-text("Applied")'):
                            logs.append("🔁 Already applied. Skipping.")
                            continue

                        easy_apply_button = page.wait_for_selector('button.jobs-apply-button', timeout=5000)
                        easy_apply_button.click()
                        time.sleep(3)

                        # Your helper calls here (inputs, dropdowns, checkboxes, resume)
                        # [Same as existing code: handle_inputs_and_textareas, etc.]

                        while True:
                            result = click_next_or_submit(page)
                            if result in ["submit", "done", "error"]:
                                break
                            human_sleep(2, 3)

                        time.sleep(3)
                    except Exception as job_e:
                        logs.append(f"❌ Error on job {job_counter}: {job_e}")
                        continue

                current_page += 1
                next_page_button = page.query_selector(f'button[aria-label=\"Page {current_page}\"]')
                if next_page_button:
                    next_page_button.click()
                    time.sleep(5)
                else:
                    logs.append("✅ Finished job pages.")
                    break

        except Exception as e:
            logs.append(f"🔥 Script error: {e}")
        finally:
            browser.close()

    return "\n".join(logs)


@tool
def get_system_time(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Get current date and time in specified format"""
    try:
        curr_time = datetime.datetime.now()
        formatted_time = curr_time.strftime(format)
        return f"Current time: {formatted_time}"
    except Exception as e:
        return f"Error getting time: {e}"

@tool
def tavily_search(query: str) -> str:

    """Search the web for current information on the given query"""
    try:
        if not query.strip():
            return "Error: Empty query provided"
        
        result = tavily_search_tool.invoke(query)
        # Format the result better
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return str(result)
        else:
            return f"Search results for '{query}': {result}"
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return f"Search error: {e}"

@tool
def llm_query(query: str) -> str:
    """Get general knowledge answer using the LLM"""
    try:
        if not query.strip():
            return "Error: Empty query provided"
        
        response = llm.invoke(query)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.error(f"LLM query error: {e}")
        return f"LLM error: {e}"

@tool
def research_and_analyze(query: str) -> str:
    """Combine web search with LLM analysis for comprehensive answers"""
    try:
        if not query.strip():
            return "Error: Empty query provided"
        
        # Get search results
        search_results = tavily_search_tool.invoke(query)
        
        # Create analysis prompt
        analysis_prompt = f"""
        Based on the following search results about "{query}", provide a comprehensive analysis:
        
        Search Results: {search_results}
        
        Please provide a clear, well-structured answer that synthesizes the information.
        """
        
        # Get LLM analysis
        analysis = llm.invoke(analysis_prompt)
        analysis_text = analysis.content if hasattr(analysis, 'content') else str(analysis)
        
        return f"Research Analysis for '{query}':\n\n{analysis_text}"
        
    except Exception as e:
        logger.error(f"Research and analysis error: {e}")
        return f"Research error: {e}"

# Initialize LLM
llm = ChatGroq(model="llama-3.3-70b-versatile")

# Try to get the standard ReAct prompt, fallback to custom
try:
    prompt_template = hub.pull("hwchase17/react")
    print("Using standard ReAct prompt")
except:
    prompt_template = my_prompt_template
    print("Using custom prompt template")

# Define tools
tools = [get_system_time, append_to_notion_page,tavily_search, llm_query, research_and_analyze, apply_linkedin_jobs,write_email,create_calendar_event,generate_and_append_note_to_notion]

# Create agent
agent = create_react_agent(llm, tools, prompt_template)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,  # Prevent infinite loops
    max_execution_time=60,
    memory=memory
    # Timeout after 60 seconds
)

def main():
    print("AI Agent is ready! Type 'exit' to quit.")
    
    print("-" * 100)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question or command.")
                continue
            
            print("\nThinking...")
            result = agent_executor.invoke(
                {"input": user_input},
                handle_parsing_errors=True
            )
            
            print(f"\nAgent: {result['output']}")
            chat_history.add_user_message(user_input)
            chat_history.add_ai_message(result["output"])
            
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            logger.error(f"Execution error: {e}")
            print(f"Sorry, I encountered an error: {e}")

if __name__ == "__main__":
    main()