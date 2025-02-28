# Universal Chatbot

## Overview
The **Universal Chatbot** is a framework for interacting with multiple AI chatbot services, including OpenAI, Grok, and Cohere. This project provides seamless switching between services, input validation, and conversation history management.

## How to Use
### Run the Chatbot
To start the chatbot, run:

```bash
python3 chatbot.py
```

### Output Example
```
Starting with Grok (model: grok-2)
Available services and models: {'grok': ['grok-2', 'grok-2-mini'], 'openai': ['gpt-4o', 'gpt-3.5-turbo', 'gpt-4-turbo'], 'cohere': ['command-r', 'command']}
[Grok:grok-2] How can I assist you today? (Type 'exit', 'help', 'switch to <service>', or 'set model <model>'):
```

### Test Commands
- `switch to openai`: Switches to OpenAI with `gpt-4o`.
- `set model gpt-3.5-turbo`: Sets OpenAI to use `gpt-3.5-turbo`.
- `switch to cohere`: Switches to Cohere with `command-r`.
- `set model command`: Sets Cohere to use `command`.

### Add New Models
Update `SERVICE_MODELS` with new model names supported by each API (check API documentation for valid models). Example for xAI: Add "grok-3" if released.

### Add New Services
- Implement a new response function (e.g., `get_anthropic_response`).
- Extend `Config`, `SERVICE_HANDLERS`, and `SERVICE_MODELS` accordingly.
- Ensure the new service’s API key is in your `.env` file.

## Notes
- **API Compatibility:** Verify model names with each service’s API documentation (e.g., OpenAI’s model list, Cohere’s model list). The ones here are examples as of early 2025.
- **Dependencies:** Add new SDKs (e.g., `pip install anthropic`) for additional services.
- **Testing:** Update `test_chatbot.py` to mock new models/services if needed.

## Running Tests
To ensure the chatbot functions correctly, a suite of unit tests is provided. You can run the tests using:

```sh
python3 -m unittest test_chatbot.py -v
```

### Test Updates for Multi-Model Support
With the updated `chatbot.py` supporting multiple models per service using the `SERVICE_MODELS` dictionary, we need to adjust the test cases in `test_chatbot.py` to reflect these changes. The primary modifications include:

- **Model Selection:** Replace references to `DEFAULT_MODELS` with `SERVICE_MODELS` and test model validation logic.
- **Service Switching:** Update tests to use the first model in the service’s model list (`SERVICE_MODELS[service][0]`).
- **Response Functions:** Ensure tests cover multiple models per service.
- **Error Handling:** Add tests for invalid model selections.

### Sample Test Output
```
test_get_cohere_response (test_chatbot.TestChatbot.test_get_cohere_response) ... ok
test_get_grok_response (test_chatbot.TestChatbot.test_get_grok_response) ... ok
test_get_openai_response (test_chatbot.TestChatbot.test_get_openai_response) ... ok
test_load_config_missing_keys (test_chatbot.TestChatbot.test_load_config_missing_keys) ... ok
test_load_config_success (test_chatbot.TestChatbot.test_load_config_success) ... ok
test_model_setting (test_chatbot.TestChatbot.test_model_setting) ... ok
test_service_switching (test_chatbot.TestChatbot.test_service_switching) ... ok
test_trim_conversation_history (test_chatbot.TestChatbot.test_trim_conversation_history) ... ok
test_validate_input_empty (test_chatbot.TestChatbot.test_validate_input_empty) ... ok
test_validate_input_invalid_chars (test_chatbot.TestChatbot.test_validate_input_invalid_chars) ... ok
test_validate_input_too_long (test_chatbot.TestChatbot.test_validate_input_too_long) ... ok
test_validate_input_valid (test_chatbot.TestChatbot.test_validate_input_valid) ... ok

Ran 12 tests in 0.254s
```

## Features Tested
- **Response Generation:** Tests responses from OpenAI, Cohere, and Grok.
- **Configuration Handling:** Ensures loading environment variables correctly.
- **Model Selection:** Validates chatbot model switching.
- **Service Switching:** Tests logic for dynamically changing chatbot services.
- **History Management:** Ensures conversation trimming works as expected.
- **Input Validation:** Checks for valid input handling, including length and character constraints.

## Contributing
If you'd like to contribute, please submit a pull request with a clear description of the changes.

## License
This project is licensed under the MIT License.

