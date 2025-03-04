import unittest
from unittest.mock import patch, Mock
import os
from chatbot import load_config, validate_input, get_response, SERVICE_HANDLERS, trim_conversation_history

class TestChatbot(unittest.TestCase):

    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "XAI_API_KEY": "test_xai_key",
            "OPENAI_API_KEY": "test_openai_key",
            "CO_API_KEY": "test_co_key"
        })
        self.env_patcher.start()
        self.config = load_config()

        self.config.co_client = Mock()
        self.config.openai_client = Mock()
        self.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]

    def tearDown(self):
        self.env_patcher.stop()

    def test_load_config_success(self):
        """Test loading config with valid environment variables."""
        config = load_config()
        self.assertEqual(config.grok_api_key, "test_xai_key")
        self.assertEqual(config.openai_api_key, "test_openai_key")
        self.assertEqual(config.co_api_key, "test_co_key")

    @patch("chatbot.load_dotenv")
    def test_load_config_missing_keys(self, mock_load_dotenv):
        """Test config loading fails with missing keys."""
        mock_load_dotenv.return_value = None  # Prevent loading .env file
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as cm:
                load_config()
            self.assertIn("Missing required environment variables", str(cm.exception))

    def test_validate_input_valid(self):
        """Test valid input passes validation."""
        valid_input = "What’s the best lock?"
        is_valid, msg = validate_input(valid_input)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_validate_input_empty(self):
        """Test empty input fails validation."""
        is_valid, msg = validate_input("")
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Input cannot be empty. Please provide some details.")

    def test_validate_input_too_long(self):
        """Test overly long input fails validation."""
        long_input = "a" * 501
        is_valid, msg = validate_input(long_input)
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Input is too long. Please keep it under 500 characters.")

    def test_validate_input_invalid_chars(self):
        """Test input with invalid characters fails validation."""
        invalid_input = "Test <script>"
        is_valid, msg = validate_input(invalid_input)
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Input contains invalid characters (e.g., <, >, {}).")

    @patch("requests.post")
    def test_get_grok_response(self, mock_post):
        """Test Grok response generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Grok response"}}]
        }
        mock_post.return_value = mock_response

        reply = get_response("Test prompt", "grok", "grok-2", False, self.conversation_history, self.config)
        self.assertEqual(reply, "Grok response")

    @patch("chatbot.OpenAI")
    def test_get_openai_response(self, mock_client_class: Mock = None, mock_client: Mock = None,):
        """Test OpenAI response generation."""
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="OpenAI response"))]
        mock_client.chat.completions.create.return_value = mock_completion
        self.config.openai_client = mock_client

        reply = get_response("Test prompt", "openai", "gpt-4o", False, self.conversation_history, self.config)
        self.assertEqual(reply, "OpenAI response")

    @patch("chatbot.cohere.Client")
    def test_get_cohere_response(self, mock_client_class: Mock = None, mock_client: Mock = None,):
        """Test Cohere response generation."""
        mock_client = Mock()
        mock_client.chat.return_value = Mock(text="Cohere response")
        self.config.co_client = mock_client

        reply = get_response("Test prompt", "cohere", "command-r", False, self.conversation_history, self.config)
        self.assertEqual(reply, "Cohere response")

    def test_trim_conversation_history(self):
        """Test conversation history trimming."""
        long_history = [{"role": "user", "content": f"Msg {i}"} for i in range(15)]
        trimmed = trim_conversation_history(long_history, max_messages=10)
        self.assertEqual(len(trimmed), 10)
        self.assertEqual(trimmed[0]["content"], "Msg 5")
        self.assertEqual(trimmed[-1]["content"], "Msg 14")

    @patch("chatbot.get_response")
    def test_service_switching(self, mock_get_response):
        """Test service switching logic (mocked response)."""
        mock_get_response.return_value = "Mocked response"
        service = "grok"
        model = "grok-2"
        user_input = "switch to openai"

        if user_input.lower().startswith("switch to "):
            new_service = user_input.lower().replace("switch to ", "").strip()
            if new_service in SERVICE_HANDLERS:
                service = new_service
                model = {"grok": "grok-2", "openai": "gpt-4o", "cohere": "command-r"}.get(service)

        self.assertEqual(service, "openai")
        self.assertEqual(model, "gpt-4o")

    @patch("chatbot.get_response")
    def test_model_setting(self, mock_get_response):
        """Test model setting logic (mocked response)."""
        mock_get_response.return_value = "Mocked response"
        model = "gpt-4o"
        user_input = "set model gpt-3.5-turbo"

        if user_input.lower().startswith("set model "):
            model = user_input.lower().replace("set model ", "").strip()

        self.assertEqual(model, "gpt-3.5-turbo")

if __name__ == "__main__":
    unittest.main()