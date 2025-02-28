# universalchatbot

# testing the universal chatbot
% python3 -m unittest test_chatbot.py -v
test_get_cohere_response (test_chatbot.TestChatbot.test_get_cohere_response)
Test Cohere response generation. ... ok
test_get_grok_response (test_chatbot.TestChatbot.test_get_grok_response)
Test Grok response generation. ... ok
test_get_openai_response (test_chatbot.TestChatbot.test_get_openai_response)
Test OpenAI response generation. ... ok
test_load_config_missing_keys (test_chatbot.TestChatbot.test_load_config_missing_keys)
Test config loading fails with missing keys. ... ok
test_load_config_success (test_chatbot.TestChatbot.test_load_config_success)
Test loading config with valid environment variables. ... ok
test_model_setting (test_chatbot.TestChatbot.test_model_setting)
Test model setting logic (mocked response). ... ok
test_service_switching (test_chatbot.TestChatbot.test_service_switching)
Test service switching logic (mocked response). ... ok
test_trim_conversation_history (test_chatbot.TestChatbot.test_trim_conversation_history)
Test conversation history trimming. ... ok
test_validate_input_empty (test_chatbot.TestChatbot.test_validate_input_empty)
Test empty input fails validation. ... ok
test_validate_input_invalid_chars (test_chatbot.TestChatbot.test_validate_input_invalid_chars)
Test input with invalid characters fails validation. ... ok
test_validate_input_too_long (test_chatbot.TestChatbot.test_validate_input_too_long)
Test overly long input fails validation. ... ok
test_validate_input_valid (test_chatbot.TestChatbot.test_validate_input_valid)
Test valid input passes validation. ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.254s
