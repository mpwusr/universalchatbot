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

# Setup logging with rotating file handler
handler = RotatingFileHandler("chatbot.log", maxBytes=10 * 1024 * 1024, backupCount=5)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)


@dataclass
class Config:
    grok_api_key: str
    openai_api_key: str
    co_api_key: str
    grok_api_url: str = "https://api.x.ai/v1/chat/completions"
    default_service: str = "grok"
    default_model: str = "grok-2"

    def __post_init__(self):
        self.co_client = cohere.Client(self.co_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def grok_headers(self):
        return {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json"
        }


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
        "I can help assess your physical security. Try asking about locks, cameras, or trends. "
        "Commands: 'help' (this message), 'exit' (quit), 'switch to <service>' (change service), "
        "'set model <model>' (change model)."
    )


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
    try:
        resp_grok: Response = requests.post(grok_url, headers=grok_headers, json=payload, timeout=10)
        resp_grok.raise_for_status()
        data = resp_grok.json()
        logger.info("Grok API response: %s", data)
        logger.info("Response time: %.2f seconds", time.time() - start_time)
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as err:
        req_error_msg = f"Oops, something broke! Error: {str(err)}. Details: {getattr(resp_grok, 'text', 'No response text')}"
        logger.error(req_error_msg)
        logger.info("Response time on failure: %.2f seconds", time.time() - start_time)
        return req_error_msg


def get_openai_response(prompt, model="gpt-4o", conversation_history=None, openai_client=None):
    if openai_client is None:
        raise ValueError("OpenAI client must be provided")
    full_prompt = build_prompt("physical security consultant", prompt, conversation_history)
    if conversation_history:
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history]
        messages.append({"role": "user", "content": full_prompt})
    else:
        messages = [{"role": "user", "content": full_prompt}]
    try:
        resp_openai = openai_client.chat.completions.create(model=model, messages=messages, max_tokens=300)
        return resp_openai.choices[0].message.content
    except Exception as e:
        raise ValueError(f"OpenAI API error: {str(e)}")


def get_cohere_response(prompt, model="command-r", conversation_history=None, co_client=None):
    if co_client is None:
        raise ValueError("Cohere client must be provided")
    base_prompt = build_prompt("physical security consultant", "", conversation_history)
    chat_history = []
    if conversation_history:
        for msg in conversation_history:
            role = "User" if msg["role"] == "user" else "Chatbot" if msg["role"] == "assistant" else "System"
            chat_history.append({"role": role, "message": msg["content"]})
    try:
        resp_co = co_client.chat(message=prompt, preamble=base_prompt, chat_history=chat_history, model=model,
                                 max_tokens=300, temperature=0.7)
        return resp_co.text
    except Exception as e:
        logger.error("Cohere API error: %s", str(e))
        return f"Oops, something broke with Cohere! Error: {str(e)}"


def trim_conversation_history(history, max_messages=10):
    return history[-max_messages:] if len(history) > max_messages else history


def fetch_x_trends(query):
    logger.info("Fetching X trends for: %s", query)
    return "Recent X posts suggest a rise in smart lock vulnerabilities (placeholder)."


SERVICE_HANDLERS = {
    "grok": get_grok_response,
    "openai": get_openai_response,
    "cohere": get_cohere_response
}


def get_response(prompt, service, model, deep_search, conversation_history, config):
    handler = SERVICE_HANDLERS.get(service)
    if not handler:
        raise ValueError(f"Unknown service: {service}")
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
        "co_client": config.co_client if service == "cohere" else None
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


if __name__ == "__main__":
    config = load_config()
    conversation_history = []
    args = parse_args()
    SERVICE = args.service
    DEFAULT_MODELS = {"grok": "grok-2", "openai": "gpt-4o", "cohere": "command-r"}
    MODEL = args.model or DEFAULT_MODELS.get(SERVICE)

    print(f"Starting with {SERVICE.capitalize()} (model: {MODEL})")
    while True:
        user_input = input(
            f"[{SERVICE.capitalize()}:{MODEL}] How can I assist you today? (Type 'exit', 'help', 'switch to <service>', or 'set model <model>'): ")
        is_valid, error_msg = validate_input(user_input)
        if not is_valid:
            print(error_msg)
            continue

        if user_input.lower() == "help":
            print_help()
        elif user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        elif user_input.lower().startswith("switch to "):
            new_service = user_input.lower().replace("switch to ", "").strip()
            if new_service in SERVICE_HANDLERS:
                SERVICE = new_service
                MODEL = DEFAULT_MODELS.get(SERVICE)
                print(f"Switched to {SERVICE.capitalize()} (model: {MODEL})")
            else:
                print(f"Service {new_service} not recognized.")
            continue
        elif user_input.lower().startswith("set model "):
            new_model = user_input.lower().replace("set model ", "").strip()
            MODEL = new_model
            print(f"Model set to {MODEL} for {SERVICE.capitalize()}")
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
                logger.exception("Error during response retrieval: %s", e)
                print(f"Sorry, something went wrong: {str(e)}")