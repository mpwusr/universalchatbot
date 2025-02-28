# Universal Chatbot

## Overview
The **Universal Chatbot** is a framework for interacting with multiple AI chatbot services, including OpenAI, Grok, and Cohere. This project provides seamless switching between services, input validation, and conversation history management.

## Running Tests
To ensure the chatbot functions correctly, a suite of unit tests is provided. You can run the tests using:

```sh
python3 -m unittest test_chatbot.py -v
```

## Test Results
Below is a sample test run output:

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


