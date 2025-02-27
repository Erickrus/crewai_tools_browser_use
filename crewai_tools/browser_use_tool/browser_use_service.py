from flask import Flask, request, jsonify
import threading
import time

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import asyncio
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

app = Flask(__name__)

# Initialize a lock to ensure only one agent call at a time
lock = threading.Lock()

# Simulate the Browser-Use agent (replace with actual logic)
def invoke_browser_use_agent(objective):
    logger.info(f"Starting Browser-Use agent with objective: {objective}")

    load_dotenv()

    async def run_search():
        agent = Agent(
            task=objective,

            browser_context=BrowserContext(
                browser=Browser(),
            ),
            llm = ChatOpenAI(
                model=os.environ['MODEL_NAME'], # 'gpt-4o-mini' 
                api_key=os.environ['OPENAI_API_KEY']
            ),
            use_vision=False,
        )
        results = await agent.run()
        return results
    # Run the async function from synchronous code
    results = asyncio.run(run_search())
    logger.info("Browser-Use agent finished.")
    return {
        "status": "success", 
        "message": f"Objective completed: {objective}",
        "results": results
    }

@app.route('/probe', methods=['GET'])
def probe():
    return "the service is alive", 200

@app.route('/browser_use_invoke', methods=['POST'])
def browser_use_invoke():
    if lock.locked():
        return jsonify({"status": "error", "message": "Browser-Use agent is currently busy. Please try again later."}), 429

    objective = request.json.get("objective")
    if not objective:
        return jsonify({"status": "error", "message": "No objective provided."}), 400

    with lock:
        result = invoke_browser_use_agent(objective)
    
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True, port=4999)