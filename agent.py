import os
from anthropic import Anthropic

client = Anthropic()

def run_job_agent():
    print("\n" + "="*60)
    print("Anthropic Job Intelligence Agent")
    print("Ask me anything about the Technical Evangelist role,")
    print("hackathons, interviews, recruiters, or the industry.")
    print("Type 'quit' to exit.")
    print("="*60 + "\n")

    conversation_history = []

    system_prompt = """You are a job intelligence agent helping someone apply for 
the Anthropic Technical Evangelist role. When the user asks a question:

1. Search the web for current, accurate information
2. Synthesize what you find into a clear, useful answer
3. Be specific — names, dates, links where possible
4. If asked about recruiters, search LinkedIn publicly visible results, 
   job postings, and conference pages to find specific names
5. Always cite where your information came from

You have access to web search. Use it for every question to ensure 
accuracy. Don't rely on your training data alone."""

    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGood luck with the application!")
            break
            
        if not user_input:
            continue

        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        print("\nAgent is researching...\n")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system_prompt,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=conversation_history
        )

        # Extract the final text response
        full_response = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_response += block.text

        print(f"Agent: {full_response}")

        # Add assistant response to history for follow-up questions
        conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        exit(1)
    run_job_agent()
