# Anthropic Job Intelligence Agent

An AI-powered research agent built to help prepare for the Anthropic Technical Evangelist role — built entirely with Claude's API.

## What It Does

- **Chat Agent** — Ask anything about the role, interviews, recruiters, or hackathons. Uses Anthropic's native web search to find real-time answers.
- **Multi-Agent Interview Prep** — Three specialized agents work in sequence: a Research Agent, Strategy Agent, and Writer Agent to produce a comprehensive interview prep document.
- **Morning Briefing** — RSS monitor collects Anthropic and Claude news in the background. Claude summarizes it into a daily briefing when you open the app.
- **Persistent Chat History** — All conversations saved to SQLite database with a sidebar like Claude.ai.

## Architecture

- **Backend:** FastAPI + Python
- **Frontend:** Single HTML file with dark mode
- **Database:** SQLite
- **AI:** Anthropic Claude API with native web search tool
- **Agents:** 5 specialized agents (chat, research, strategy, writer, briefing)

## Setup

1. Clone the repo
2. Install dependencies: `pip install fastapi uvicorn anthropic requests`
3. Set your API key: `export ANTHROPIC_API_KEY=your_key`
4. Run: `python3 main.py`
5. Open browser to `http://localhost:8000`

## Built With

- [Anthropic Claude API](https://anthropic.com)
- FastAPI
- SQLite
