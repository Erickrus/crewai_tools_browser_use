import datetime
import json
import os
import logging
from typing import Any, Type

import requests

import urllib
import traceback

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
    
    def run(self, browser_use_objective):
        try:
            response = requests.post(
                self.url, json={
                    "browser_use_objective": browser_use_objective
                }
            )
            if response.status_code == 200:
                results = response.json()
                return results
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return {}
        except requests.exceptions.RequestException as e:
            # Handle any exceptions that occur during the request
            logger.error(f"An error occurred: {e}")
            return {}

class BrowserUseToolSchema(BaseModel):
    """Input for BrowserUseTool."""

    browser_use_objective: str = Field(
        ..., description="Mandatory objective description for browser-use to execute command"
    )

class BrowserUseTool(BaseTool):
    name: str = """Use "BrowserUse" to do the GUI Automation based on web browser"""
    description: str = (
        "A tool to complete automation task on web browser autonoumously. "
        "param: browser_use_objective is used to define the general task for the automation, "
        "and this param is usually some detailed steps of a web automations. "
        "usually specified in multi-line, in the form of a numbered list e.g. 1, 2, 3, ... "
        "with each line representing a step"
    )
    args_schema: Type[BaseModel] = BrowserUseToolSchema

    def _run(self, **kwargs: Any) -> Any:
        """Execute the GUI automation operation."""
        browser_use_objective = kwargs.get("browser_use_objective")

        results = {}

        try:
            browserUseApi = BrowserUseAPI(
                url = os.environ["BROWSER_USE_API_URL"]
            )
            results = browserUseApi.run(browser_use_objective)
        except:
            pass
        formatted_results = {
            "browser_use_objective": browser_use_objective
        }

        formatted_results["result"] = results

        return formatted_results