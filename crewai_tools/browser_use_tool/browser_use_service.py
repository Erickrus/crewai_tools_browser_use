import asyncio
import logging
import os
import time
import threading
import uuid
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

load_dotenv()

app = Flask(__name__)

# Task storage to keep track of tasks
tasks = {}

# Initialize a thread pool executor for running tasks in the background
executor = ThreadPoolExecutor(max_workers=1)

# Function to process the task in the background
def process_task(task_id, objective):
    logger.info(f"Starting Browser-Use agent with objective: {objective}")

    async def run_browser_use():
        agent = Agent(
            task=objective,
            browser_context=BrowserContext(
                browser=Browser(),
            ),
            llm=ChatOpenAI(
                model=os.environ['MODEL_NAME'],  # 'gpt-4o-mini'
                api_key=os.environ['OPENAI_API_KEY']
            ),
            use_vision=False,
        )
        results = await agent.run()
        return results

    # Run the async function
    results = asyncio.run(run_browser_use())
    logger.info("Browser-Use agent finished.")

    # Update the task status and results
    tasks[task_id] = {
        "status": "completed",
        "message": f"Objective completed: {objective}",
        "results": results
    }

@app.route('/probe', methods=['GET'])
def probe():
    return "browser_use_service is alive", 200

@app.route('/browser_use_invoke', methods=['POST'])
def browser_use_invoke():
    objective = request.json.get("objective")
    if not objective:
        return jsonify({"status": "error", "message": "No objective provided."}), 400

    # Generate a unique task ID
    task_id = str(uuid.uuid4())

    # Initialize the task with "processing" status
    tasks[task_id] = {"status": "processing"}

    # Submit the task to the thread pool executor
    executor.submit(process_task, task_id, objective)

    # Return the task ID immediately
    return jsonify({"status": "processing", "task_id": task_id}), 202

@app.route('/browser_use_status/<task_id>', methods=['GET'])
def browser_use_status(task_id):
    if task_id not in tasks:
        return jsonify({"status": "error", "message": "Task ID not found."}), 404

    task = tasks[task_id]
    if task["status"] == "processing":
        return jsonify({"status": "processing"}), 202
    elif task["status"] == "completed":
        return jsonify(task), 200

if __name__ == '__main__':
    app.run(debug=True, port=4999)
