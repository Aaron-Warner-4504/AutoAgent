
# 🤖 AutoAgent – AI-Powered Browser Automation Agent

AutoAgent is a fully autonomous AI assistant that automates browser-based and productivity tasks using natural language instructions. It combines powerful LLM reasoning, real-time web automation, and persistent memory to perform complex actions — just like a human assistant.

## 🚀 Features

- 🧠 **LLM Integration (Groq via LangChain)**: Fast, efficient decision-making and prompt understanding.
- 🌐 **Browser Automation (Playwright)**: Automates multi-step web tasks like logging in, scraping, or form submissions.
- 📅 **Google Calendar API**: Schedule and manage meetings or reminders via natural language.
- 🗂 **Notion SDK Integration**: Automatically update or fetch content from Notion databases.
- 💾 **Memory via Firestore**: Agent now retains memory across sessions, enabling contextual understanding and continuity.
- 🧰 **Custom Tools**: Easily extendable with additional APIs or automation logic.

## 📺 Demo

Check out the demo video here:  
[![AutoAgent Demo](https://img.youtube.com/vi/njlc8-r3hGw/0.jpg)](https://youtu.be/njlc8-r3hGw?si=Mlgu-g8m-IvMnWPV)

## 🔧 Tech Stack

- Python
- LangChain + Groq
- Playwright
- Google Calendar API
- Firestore (for memory)
- Notion SDK
- dotenv

## 📂 Directory Structure

```
agents_5/
├── finalagent.py
├── tools/
├── utils/
└── .env
```

## 💡 How It Works

1. User enters a natural language command.
2. Agent processes the prompt and decides the appropriate tool/action.
3. Executes the task using browser automation or API calls.
4. Saves memory (if enabled) via Firestore.
5. Supports follow-up queries using stored context.

## 🛠 Setup Instructions

1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up `.env` with required API keys and credentials.
4. Run the agent:
```bash
python finalagent.py
```

## 🔮 Roadmap

- Voice command integration 🎙️
- Visual dashboard UI
- Email and file automation tools
- Chrome plugin version

## 🧠 Example Use Cases

- “Schedule a team sync at 5 PM tomorrow.”
- “Update the sprint status in Notion.”
- “Open my GitHub dashboard.”

## 🙌 Contribution

Feel free to fork, extend tools, or suggest features. PRs welcome!

## 📫 Contact

Built by [Pranav Kodlinge](https://www.linkedin.com/in/pranavkodlinge)  
Let's automate the future.

---

#AutoAgent #LangChain #Playwright #Groq #Python #AIagent #Automation #GenAI #LLM #Firestore #NotionSDK #GoogleCalendarAPI #buildinpublic
