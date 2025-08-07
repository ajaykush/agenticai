from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://ajay-kush-ai-project-resource.services.ai.azure.com/api/projects/ajay_kush_ai_project")

agent = project.agents.get_agent("asst_QqiBHle0Anlh93ycpIIiTpb8")

thread = project.agents.threads.create()

print("Welcome to your AI Agent Chat! Type 'exit' to quit.")

while True: 
    user_input = input("\nYou: ")

    if user_input.strip().lower() == "exit":
        print("Goodbye!")
        break
    
    #Send user message
    message = project.agents.messages.create( 
        thread_id=thread.id, 
        role="user",
        content=user_input
    )

    #Run the agent on this thread
    run = project.agents.runs.create_and_process( 
        thread_id=thread.id, 
        agent_id=agent.id
    )

    #If the agent fails, print error
    if run.status == "failed":
        print(f"Agent Run failed: {run.last_error}")
        continue

    messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    # Find the most recent assistant message
    agent_response = None
    for msg in reversed(list(messages)):
            if msg.role != "user" and msg.text_messages:
                agent_response = msg.text_messages[-1].text.value
                break

    if agent_response:
        print(f"\nAgent: {agent_response}")
    else:
        print(f"\nAgent:(No response or output from the agent.)")

