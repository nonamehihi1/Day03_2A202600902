"""
Web UI for Chatbot vs ReAct Agent using Gradio.
Run this script to launch an interactive web demo.
"""
import os
import gradio as gr
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import the main logic
from main import get_provider, get_tools
from src.chatbot import Chatbot
from src.agent.agent import ReActAgent
from src.telemetry.metrics import tracker

def init_systems():
    try:
        provider = get_provider()
        tools = get_tools()
        chatbot = Chatbot(llm=provider)
        agent = ReActAgent(llm=provider, tools=tools, max_steps=8)
        return chatbot, agent, f"Connected to {provider.__class__.__name__}"
    except Exception as e:
        return None, None, f"Error initializing: {str(e)}"

# Initialize globally
global_chatbot, global_agent, init_status = init_systems()

def process_message(message, history, system_choice):
    if not message.strip():
        return history + [("", "Please enter a message.")]
    
    if global_chatbot is None or global_agent is None:
        return history + [(message, "System is not properly initialized. Check your API keys and .env file.")]
        
    try:
        if system_choice == "Chatbot (Baseline)":
            response = global_chatbot.chat(message)
        else:
            response = global_agent.run(message)
            
        return history + [(message, response)]
    except Exception as e:
        error_msg = f"Error during execution: {str(e)}"
        return history + [(message, error_msg)]

# Create the Gradio interface
with gr.Blocks(title="AI Agent Lab: Chatbot vs ReAct Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 AI Agent Lab: Chatbot vs ReAct Agent")
    gr.Markdown("Test the difference between a standard LLM Chatbot and an Agent equipped with tools!")
    gr.Markdown(f"**Status:** {init_status}")
    
    with gr.Row():
        with gr.Column(scale=1):
            system_selector = gr.Radio(
                choices=["Chatbot (Baseline)", "ReAct Agent (Tools)"],
                value="ReAct Agent (Tools)",
                label="Select System",
                info="Chatbot has no tools. Agent has Flight, Hotel, Promo, Calculator, Wikipedia, and Weather tools."
            )
            
            gr.Markdown("""
            ### Try asking:
            - **Simple:** How much is a flight from Hanoi to Paris?
            - **Multi-step (Agent):** I want to fly from Hanoi to Paris, stay for 3 nights, and use the promo code SUMMER. What is the total cost?
            - **Web & Weather (Agent):** Who is the CEO of Apple? Also what is the current weather in New York?
            """)
            
        with gr.Column(scale=2):
            chatbot_ui = gr.Chatbot(height=500)
            msg_input = gr.Textbox(placeholder="Ask something...", label="Your Message")
            clear_btn = gr.ClearButton([msg_input, chatbot_ui])

    msg_input.submit(process_message, [msg_input, chatbot_ui, system_selector], [chatbot_ui])

if __name__ == "__main__":
    print("🚀 Launching Web UI on http://127.0.0.1:7860")
    demo.launch(server_name="0.0.0.0", server_port=7860)
