import datetime
import json
import os
import logging
import requests
import time
import uuid
from typing import Any, Type

from dotenv import load_dotenv
load_dotenv()

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BrowserUseAPI:
    def __init__(self, url):
        self.url = url

    def submit_task(self, browser_use_objective):
        """Submit a task and get a task_id."""
        try:
            logger.info(f"{self.url}/submit")
            response = requests.post(
                f"{self.url}/submit",
                json={"browser_use_objective": browser_use_objective}
            )
            if response.status_code == 202:
                return response.json().get("task_id")
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None

    def query_task_status(self, task_id):
        """Query the status of a task using task_id."""
        try:
            logger.info(f"{self.url}/query/{task_id}")
            response = requests.get(f"{self.url}/query/{task_id}")
            if response.status_code == 200:
                return {"status": "completed", "message":"completed", "data": response.json()}
            elif response.status_code == 202:
                return {"status": "processing", "message":"processing"}
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return {"status": "error", "message": f"Unexpected status code: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return {"status": "error", "message": f"An error occurred: {str(e)}"}


class BrowserUseToolSchema(BaseModel):
    """Input for BrowserUseTool."""

    browser_use_objective: str = Field(
        ..., description="Mandatory objective description for browser-use to execute command"
    )


class BrowserUseTool(BaseTool):
    name: str = """A tool to do the GUI Automation based on web browser"""
    description: str = (
        "A tool to complete GUI automation task on web browser autonomously. "
        "param: browser_use_objective is used to define the general task for the automation, "
        "and this param is usually some detailed steps of a web automation. "
        "usually specified in multi-line, in the form of a numbered list e.g. 1, 2, 3, ... "
        "with each line representing a step"
    )
    args_schema: Type[BaseModel] = BrowserUseToolSchema

    def _run(self, **kwargs: Any) -> Any:
        """Execute the GUI automation instructions on a web browser."""
        browser_use_objective = kwargs.get("browser_use_objective")
        timeout = 300  # 5 minutes timeout
        check_interval = 2  # Check status every 1 second

        try:
            browser_use_api = BrowserUseAPI(url=os.environ["BROWSER_USE_API_URL"])
            task_id = browser_use_api.submit_task(browser_use_objective)

            if not task_id:
                return {
                    "status": "error", 
                    "browser_use_objective": browser_use_objective,
                    "result": {},
                    "message": "Failed to submit task"
                }

            start_time = time.time()
            while time.time() - start_time < timeout:
                status = browser_use_api.query_task_status(task_id)
                if status.get("status") == "completed":
                    return {
                        "status": "success",
                        "browser_use_objective": browser_use_objective,
                        "result": status.get("results"),
                        "message": status.get("message")
                    }
                elif status.get("status") == "processing":
                    time.sleep(check_interval)
                else:
                    return {
                        "status": "error", 
                        "message": "Unknown status",
                        "result": {},
                        "browser_use_objective": browser_use_objective
                    }

            return {
                "status": "error", 
                "message": "Task timed out", 
                "result": {},
                "browser_use_objective": browser_use_objective
            }
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {
                "status": "error", 
                "message": f"An error occurred: {str(e)}", 
                "result": {},
                "browser_use_objective": browser_use_objective
            }
