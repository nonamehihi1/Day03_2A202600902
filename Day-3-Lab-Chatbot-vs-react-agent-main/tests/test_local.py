import os
import sys
from dotenv import load_dotenv

# Add src to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from src.core.local_provider import LocalProvider
from src.agent.agent import ReActAgent
from main import get_tools # Tái sử dụng tools bạn đã define ở main.py

def test_local_agent():
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
    
    print(f"--- Testing ReAct Agent with Local Provider ---")
    print(f"Model Path: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"❌ Error: Model file not found at {model_path}")
        print("Please download it from Hugging Face and place it in the models/ folder.")
        return

    try:
        # 1. Khởi tạo LLM Provider
        provider = LocalProvider(model_path=model_path)
        
        # 2. Khởi tạo Agent và gắn Tools
        tools = get_tools()
        agent = ReActAgent(llm=provider, tools=tools, max_steps=10)
        
        # 3. Câu hỏi chứng tỏ khả năng dùng Wikipedia Tool
        prompt = "Who is the CEO of Apple? Search Wikipedia for 'Apple Inc.' to find out."
        print(f"\n User: {prompt}\n")
        print(" Agent is thinking (Thought-Action-Observation loop)...\n")
        
        # 4. Chạy Agent
        answer = agent.run(prompt)
        print(f"\n Final Answer:\n{answer}")
        
    except Exception as e:
        print(f"\n Error during execution: {e}")

if __name__ == "__main__":
    test_local_agent()
