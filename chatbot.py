import os
import logging
import requests
from dotenv import load_dotenv
import time
from dataclasses import dataclass
from openai import OpenAI
import cohere
from requests import Response
from tenacity import retry, stop_after_attempt, wait_exponential
import re
from logging.handlers import RotatingFileHandler
import argparse
import inspect

# Setup logging
handler = RotatingFileHandler("chatbot.log", maxBytes=10 * 1024 * 1024, backupCount=5)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)


@dataclass
class Config:
    grok_api_key: str
    openai_api_key: str
    co_api_key: str
    # Add new service keys here (e.g., anthropic_api_key)
    grok_api_url: str = "https://api.x.ai/v1/chat/completions"
    default_service: str = "grok"

    def __post_init__(self):
        self.co_client = cohere.Client(self.co_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        # Add new clients here (e.g., self.anthropic_client = anthropic.Client(self.anthropic_api_key))

    def grok_headers(self):
        return {"Authorization": f"Bearer {self.grok_api_key}", "Content-Type": "application/json"}


def load_config():
    load_dotenv()
    grok_key = os.getenv("XAI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    co_key = os.getenv("CO_API_KEY")
    missing_keys = []
    if not grok_key:
        missing_keys.append("XAI_API_KEY")
    if not openai_key:
        missing_keys.append("OPENAI_API_KEY")
    if not co_key:
        missing_keys.append("CO_API_KEY")
    if missing_keys:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
    return Config(grok_api_key=grok_key, openai_api_key=openai_key, co_api_key=co_key)


def print_help():
    print(
        "I can help assess your physical security. Commands: 'help', 'exit', 'switch to <service>', 'set model <model>'.")


# Existing functions (unchanged for brevity)
def build_prompt(base_role, prompt, conversation_history=None, extra_instructions=""):
    base_prompt = f"Act as a {base_role}. {extra_instructions}"
    if conversation_history:
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        return f"{history_text}\n{base_prompt}{prompt}"
    return base_prompt + prompt


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_grok_response(prompt, model, use_deep_search=False, conversation_history=None, grok_url=None,
                      grok_headers=None):
    start_time = time.time()
    extra = "Use DeepSearch to analyze recent X posts and provide insights. " if use_deep_search else ""
    full_prompt = build_prompt("physical security consultant", prompt, conversation_history, extra)
    payload = {"model": model, "messages": [{"role": "user", "content": full_prompt}], "max_tokens": 300}
    logger.info("Sending payload to Grok: %s", payload)
    resp_grok = None
    try:
        resp_grok = requests.post(grok_url, headers=grok_headers, json=payload, timeout=10)
        resp_grok.raise_for_status()
        data = resp_grok.json()
        logger.info("Grok API response: %s", data)
        logger.info("Response time: %.2f seconds", time.time() - start_time)
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as err:
        req_error_msg = f"Oops, something broke! Error: {str(err)}. Details: {getattr(resp_grok, 'text', 'No response text') if resp_grok else 'No response received'}"
        logger.error(req_error_msg)
        logger.info("Response time on failure: %.2f seconds", time.time() - start_time)
        return req_error_msg


def get_openai_response(prompt, model, conversation_history=None, openai_client=None):
    if openai_client is None:
        raise ValueError("OpenAI client must be provided")
    full_prompt = build_prompt("physical security consultant", prompt, conversation_history)
    messages = [{"role": "user", "content": full_prompt}]
    if conversation_history:
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history] + messages
    try:
        resp_openai = openai_client.chat.completions.create(model=model, messages=messages, max_tokens=300)
        return resp_openai.choices[0].message.content
    except Exception as e:
        raise ValueError(f"OpenAI API error: {str(e)}")


def get_cohere_response(prompt, model, conversation_history=None, co_client=None):
    if co_client is None:
        raise ValueError("Cohere client must be provided")
    base_prompt = build_prompt("physical security consultant", "", conversation_history)
    chat_history = [{"role": "User" if msg["role"] == "user" else "Chatbot", "message": msg["content"]} for msg in
                    conversation_history] if conversation_history else []
    try:
        resp_co = co_client.chat(message=prompt, preamble=base_prompt, chat_history=chat_history, model=model,
                                 max_tokens=300, temperature=0.7)
        return resp_co.text
    except Exception as e:
        logger.error("Cohere API error: %s", str(e))
        return f"Oops, something broke with Cohere! Error: {str(e)}"


# New service example: Anthropic (hypothetical, requires anthropic SDK)
def get_anthropic_response(prompt, model, conversation_history=None, anthropic_client=None):
    if anthropic_client is None:
        raise ValueError("Anthropic client must be provided")
    full_prompt = build_prompt("physical security consultant", prompt, conversation_history)
    messages = [{"role": "user", "content": full_prompt}]
    if conversation_history:
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history] + messages
    try:
        # Hypothetical Anthropic API call (adjust based on actual SDK)
        response = anthropic_client.complete(prompt=full_prompt, model=model, max_tokens=300)
        return response["text"]
    except Exception as e:
        logger.error("Anthropic API error: %s", str(e))
        return f"Oops, something broke with Anthropic! Error: {str(e)}"


SERVICE_HANDLERS = {
    "grok": get_grok_response,
    "openai": get_openai_response,
    "cohere": get_cohere_response,
    # "anthropic": get_anthropic_response  # Uncomment and configure if adding Anthropic
}

# Expanded model options
SERVICE_MODELS = {
    "grok": ["grok-2", "grok-2-mini"],  # Example xAI models
    "openai": ["gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo"],
    "cohere": ["command-r", "command"],
    # "anthropic": ["claude-3-opus", "claude-3-sonnet"]  # Uncomment for Anthropic
}


def get_response(prompt, service, model, deep_search, conversation_history, config):
    handler = SERVICE_HANDLERS.get(service)
    if not handler:
        raise ValueError(f"Unknown service: {service}")
    if model not in SERVICE_MODELS.get(service, []):
        raise ValueError(f"Model {model} not supported for {service}")
    if deep_search:
        prompt += f"\nAdditional context: {fetch_x_trends(prompt)}"

    args = {
        "prompt": prompt,
        "model": model,
        "use_deep_search": deep_search,
        "conversation_history": conversation_history,
        "grok_url": config.grok_api_url if service == "grok" else None,
        "grok_headers": config.grok_headers() if service == "grok" else None,
        "openai_client": config.openai_client if service == "openai" else None,
        "co_client": config.co_client if service == "cohere" else None,
        # "anthropic_client": config.anthropic_client if service == "anthropic" else None
    }

    sig = inspect.signature(handler)
    filtered_args = {k: v for k, v in args.items() if k in sig.parameters}
    return handler(**filtered_args)


def validate_input(user_input):
    if not user_input.strip():
        return False, "Input cannot be empty. Please provide some details."
    if len(user_input) > 500:
        return False, "Input is too long. Please keep it under 500 characters."
    if re.search(r'[<>{}]', user_input):
        return False, "Input contains invalid characters (e.g., <, >, {})."
    return True, ""


def parse_args():
    parser = argparse.ArgumentParser(description="Universal Chatbot for Physical Security")
    parser.add_argument("--service", default="grok", choices=["grok", "openai", "cohere"], help="AI service to use")
    parser.add_argument("--model", default=None, help="Model to use (overrides default)")
    return parser.parse_args()

def trim_conversation_history(history, max_messages=10):
    return history[-max_messages:] if len(history) > max_messages else history


def fetch_x_trends(query):
    logger.info("Fetching X trends for: %s", query)
    return "Recent X posts suggest a rise in smart lock vulnerabilities (placeholder)."


if __name__ == "__main__":
    config = load_config()
    conversation_history = []
    args = parse_args()
    SERVICE = args.service
    MODEL = args.model or SERVICE_MODELS[SERVICE][0]  # Default to first model in list

    print(f"Starting with {SERVICE.capitalize()} (model: {MODEL})")
    print(f"Available services and models: {SERVICE_MODELS}")
    while True:
        user_input = input(
            f"[{SERVICE.capitalize()}:{MODEL}] How can I assist you today? (Type 'exit', 'help', 'switch to <service>', or 'set model <model>'): ")
        is_valid, error_msg = validate_input(user_input)
        if not is_valid:
            print(error_msg)
            continue

        if user_input.lower() == "help":
            print_help()
            print(f"Available services and models: {SERVICE_MODELS}")
        elif user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        elif user_input.lower().startswith("switch to "):
            new_service = user_input.lower().replace("switch to ", "").strip()
            if new_service in SERVICE_HANDLERS:
                SERVICE = new_service
                MODEL = SERVICE_MODELS[SERVICE][0]  # Default to first model of new service
                print(f"Switched to {SERVICE.capitalize()} (model: {MODEL})")
            else:
                print(f"Service {new_service} not recognized. Available: {list(SERVICE_HANDLERS.keys())}")
            continue
        elif user_input.lower().startswith("set model "):
            new_model = user_input.lower().replace("set model ", "").strip()
            if new_model in SERVICE_MODELS[SERVICE]:
                MODEL = new_model
                print(f"Model set to {MODEL} for {SERVICE.capitalize()}")
            else:
                print(f"Model {new_model} not available for {SERVICE}. Options: {SERVICE_MODELS[SERVICE]}")
            continue
        else:
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history = trim_conversation_history(conversation_history)
            deep_search = "trend" in user_input.lower()
            try:
                reply = get_response(user_input, SERVICE, MODEL, deep_search, conversation_history, config)
                print(f"{SERVICE.capitalize()} says: {reply}")
                conversation_history.append({"role": "assistant", "content": reply})
            except Exception as e:
                logger.exception("Error: %s", e)
                print(f"Sorry, something went wrong: {str(e)}")