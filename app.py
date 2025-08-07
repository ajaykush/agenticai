import os
import chainlit as cl
import logging
from dotenv import load_dotenv  # For loading environment variables
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

# Load environment variables from a .env file (for connection string and agent ID)
# load_dotenv() 

# Disable verbose connection logs for cleaner output
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Retrieve Azure AI Project connection details from environment variables
# AIPROJECT_ENDPOINT = os.getenv("AIPROJECT_ENDPOINT")
# AIPROJECT_PROJECT_NAME = os.getenv("AIPROJECT_PROJECT_NAME")
AGENT_ID = os.getenv("AGENT_ID")

# Initialize the Azure AI Project client
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://ajay-kush-ai-project-resource.services.ai.azure.com/api/projects/ajay_kush_ai_project")


# Chainlit setup - this decorator marks the function to be executed when a new chat session starts
@cl.on_chat_start
async def on_chat_start():
    # Retrieve agent using the stored ID
    agent = project.agents.get_agent("asst_QqiBHle0Anlh93ycpIIiTpb8")

    # Store agent and create a new thread for the chat session if not already done
    if not cl.user_session.get("agent"):
        cl.user_session.set("agent", agent)
    if not cl.user_session.get("thread_id"):
        thread = project.agents.threads.create()
        cl.user_session.set("thread_id", thread.id)
        await cl.Message(
            content=f"Welcome! Chat with your AI Agent (Agent ID: {AGENT_ID})!",
            author="System"
        ).send()

# This decorator marks the function to be executed when a new message is received from the user
@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")

    # Send a "thinking" message to the user while the agent processes
    msg = cl.Message(content="", author="Agent")
    await msg.send()

    try:
        # Send user message to the Azure AI agent thread
        project.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=message.content
        )

        # Run the agent to process the thread
        run = project.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=agent.id
        )

        # Handle agent run failure
        if run.status == "failed":
            raise Exception(run.last_error)

        # Retrieve all messages from the thread
        messages = project.agents.messages.list(thread_id=thread_id, order=ListSortOrder.ASCENDING)
        
        # Find the most recent agent message
        agent_response = None
        for msg_item in reversed(list(messages)):
            if msg_item.role != "user" and msg_item.text_messages:
                agent_response = msg_item.text_messages[-1].text.value
                break
        
        # Update the thinking message with the actual agent response
        if agent_response:
            msg.content = agent_response
        else:
            msg.content = "(No response or output from the agent.)"
        await msg.update()

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()