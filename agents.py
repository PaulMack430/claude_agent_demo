import os
from anthropic import Anthropic

client = Anthropic()

def research_agent(topic: str, progress_callback=None) -> str:
    if progress_callback:
        progress_callback("🔍 Research Agent: Searching the web...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="You are a research agent. Search the web and gather comprehensive information about the given topic. Output a structured research report.",
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": f"Research this thoroughly: {topic}"}]
    )
    result = ""
    for block in response.content:
        if hasattr(block, "text"):
            result += block.text
    if progress_callback:
        progress_callback(f"✅ Research Agent: Complete — gathered {len(result.split())} words")
    return result

def strategy_agent(research: str, background: str, progress_callback=None) -> str:
    if progress_callback:
        progress_callback("🧠 Strategy Agent: Analyzing your background against the role...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="You are a career strategy agent. Map research about a job to a candidate's background. Identify matches, gaps, key stories, and differentiating angles.",
        messages=[{"role": "user", "content": f"Research:\n{research}\n\nCandidate background:\n{background}\n\nCreate a strategic interview prep plan."}]
    )
    result = ""
    for block in response.content:
        if hasattr(block, "text"):
            result += block.text
    if progress_callback:
        progress_callback("✅ Strategy Agent: Complete — identified key talking points")
    return result

def writer_agent(research: str, strategy: str, progress_callback=None) -> str:
    if progress_callback:
        progress_callback("✍️ Writer Agent: Creating your interview prep document...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system="You are a professional career coach. Create a polished comprehensive interview prep document with talking points, stories to tell, questions to ask, and a one-page summary for the night before.",
        messages=[{"role": "user", "content": f"Research:\n{research}\n\nStrategy:\n{strategy}\n\nWrite a comprehensive interview prep document."}]
    )
    result = ""
    for block in response.content:
        if hasattr(block, "text"):
            result += block.text
    if progress_callback:
        progress_callback("✅ Writer Agent: Complete — your prep document is ready!")
    return result

def run_interview_prep_pipeline(candidate_background: str, progress_callback=None) -> dict:
    if progress_callback:
        progress_callback("🚀 Starting 3-agent pipeline...")
    topic = """The Anthropic Technical Evangelist (Startups) role. Include:
    - What the role involves day to day
    - Interview process and questions asked
    - What Anthropic looks for in candidates
    - Company culture and values
    - Recent Anthropic news relevant to this role"""
    research = research_agent(topic, progress_callback)
    strategy = strategy_agent(research, candidate_background, progress_callback)
    document = writer_agent(research, strategy, progress_callback)
    if progress_callback:
        progress_callback("🎉 All agents complete! Your prep document is below.")
    return {"research": research, "strategy": strategy, "document": document}

