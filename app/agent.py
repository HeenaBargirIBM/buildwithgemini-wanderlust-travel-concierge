# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


from app.firestore_tools import (
    add_destination,
    get_destination_details,
    search_destinations,
)
from app.image_tools import (
    generate_destination_postcard,
    generate_destination_video,
)


import json
import urllib.parse
import urllib.request


def get_destination_weather(location: str) -> str:
    """Fetches real-time weather information and forecast for any city or destination worldwide.

    Args:
        location: City name or destination location (e.g. 'Kyoto', 'Paris', 'New York', 'Tokyo').

    Returns:
        A string with the live weather report including temperature and current conditions.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location)}&count=1&language=en&format=json"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "WanderlustConcierge/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))

        if not geo_data.get("results"):
            return f"Could not find coordinates for location '{location}'."

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        name, country = loc["name"], loc.get("country", "")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req_w = urllib.request.Request(weather_url, headers={"User-Agent": "WanderlustConcierge/1.0"})
        with urllib.request.urlopen(req_w, timeout=5) as resp:
            weather_data = json.loads(resp.read().decode("utf-8"))

        current = weather_data.get("current_weather", {})
        temp_c = current.get("temperature")
        temp_f = round((temp_c * 9 / 5) + 32, 1) if temp_c is not None else None

        code = current.get("weathercode", 0)
        conditions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow",
            80: "Rain showers", 95: "Thunderstorm"
        }.get(code, "Variable weather")

        return f"Current weather in {name}{', ' + country if country else ''}: {temp_c}°C ({temp_f}°F), {conditions}."
    except Exception as e:
        return f"Error fetching live weather for {location}: {str(e)}"


import os


def get_exchange_rates(base_currency: str = "USD", target_currencies: str = "EUR,JPY,GBP,CAD,AUD") -> dict:
    """Fetches real-time foreign currency exchange rates for travel budget conversions.

    Args:
        base_currency: 3-letter currency code for source currency (e.g. 'USD', 'EUR', 'GBP').
        target_currencies: Comma-separated list of target currency codes (e.g. 'EUR,JPY,GBP').

    Returns:
        A dictionary containing live exchange rates and base currency info.
    """
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    base = base_currency.upper().strip()
    targets = target_currencies.upper().strip()

    try:
        if api_key:
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
        else:
            url = f"https://api.frankfurter.app/latest?from={base}&to={targets}"

        req = urllib.request.Request(url, headers={"User-Agent": "WanderlustConcierge/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if api_key:
            all_rates = data.get("conversion_rates", {})
            target_list = [t.strip() for t in targets.split(",") if t.strip()]
            filtered_rates = {k: all_rates[k] for k in target_list if k in all_rates}
            return {"base_currency": base, "rates": filtered_rates}
        else:
            return {
                "base_currency": base,
                "date": data.get("date"),
                "rates": data.get("rates", {}),
            }
    except Exception as e:
        return {"error": f"Failed to fetch exchange rates for {base}: {str(e)}"}


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from pathlib import Path
from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)

# Load code executor configuration from deployment_metadata.json
metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
code_executor = None

if metadata_path.exists():
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        sandbox_res = meta.get("sandbox_resource_name")
        agent_engine_res = meta.get("remote_agent_runtime_id")

        if sandbox_res:
            code_executor = AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_res)
        elif agent_engine_res:
            code_executor = AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_res)


from google.adk.agents.callback_context import CallbackContext
from google.adk.memory import VertexAiMemoryBankService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        logger.warning(f"Memory service not available or failed to add session to memory: {e}")
    return None


def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-60f927bb363e",
        location="us-east1",
        agent_engine_id="7489712679712456704",
    )


from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from app.a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Wanderlust Travel Concierge, an expert AI travel agent. "
        "Help travelers discover destinations, search catalog records, get destination details, "
        "add new destinations, generate scenic postcard image visuals, check real-time weather forecasts, convert foreign currency exchange rates, check local time, "
        "or write and execute Python code in a safe sandbox environment for complex calculations or data analysis. "
        "IMPORTANT: Always remember, store, and recall all user allergies (including food allergies, medical conditions, dietary restrictions, and environmental sensitivities) "
        "across sessions. Whenever a traveler states an allergy, acknowledge it and ensure all future travel, dining, or activity recommendations strictly accommodate their allergies."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="wanderlust_travel_concierge",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        get_destination_weather,
        generate_destination_postcard,
        generate_destination_video,
        get_exchange_rates,
        get_current_time,
        search_destinations,
        get_destination_details,
        add_destination,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


