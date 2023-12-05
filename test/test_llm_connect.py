import os
import openai
from openai._exceptions import NotFoundError
from biochatter.llm_connect import (
    GptConversation,
    AzureGptConversation,
    SystemMessage,
    HumanMessage,
    AIMessage,
    XinferenceConversation,
)
import pytest
from unittest.mock import patch, Mock


@pytest.fixture(scope="module", autouse=True)
def manageTestContext():
    import openai

    base_url = openai.base_url
    api_type = openai.api_type
    api_version = openai.api_version
    api_key = openai.api_key
    # api_key_path = openai.api_key_path
    organization = openai.organization
    yield True

    openai.base_url = base_url
    openai.api_type = api_type
    openai.api_version = api_version
    openai.api_key = api_key
    # openai.api_key_path = api_key_path
    openai.organization = organization


def test_empty_messages():
    convo = GptConversation(
        model_name="gpt-3.5-turbo",
        prompts={},
        split_correction=False,
    )
    assert convo.get_msg_json() == "[]"


def test_single_message():
    convo = GptConversation(
        model_name="gpt-3.5-turbo",
        prompts={},
        split_correction=False,
    )
    convo.messages.append(SystemMessage(content="Hello, world!"))
    assert convo.get_msg_json() == '[{"system": "Hello, world!"}]'


def test_multiple_messages():
    convo = GptConversation(
        model_name="gpt-3.5-turbo",
        prompts={},
        split_correction=False,
    )
    convo.messages.append(SystemMessage(content="Hello, world!"))
    convo.messages.append(HumanMessage(content="How are you?"))
    convo.messages.append(AIMessage(content="I'm doing well, thanks!"))
    assert convo.get_msg_json() == (
        '[{"system": "Hello, world!"}, '
        '{"user": "How are you?"}, '
        '{"ai": "I\'m doing well, thanks!"}]'
    )


def test_unknown_message_type():
    convo = GptConversation(
        model_name="gpt-3.5-turbo",
        prompts={},
        split_correction=False,
    )
    convo.messages.append(None)
    with pytest.raises(ValueError):
        convo.get_msg_json()


@patch("biochatter.llm_connect.openai.OpenAI")
def test_openai_catches_authentication_error(mock_openai):
    mock_openai.return_value.models.list.side_effect = openai._exceptions.AuthenticationError(
        "Incorrect API key provided: fake_key. You can find your API key at https://platform.openai.com/account/api-keys.",
        response=Mock(),
        body=None
    )
    convo = GptConversation(
        model_name="gpt-3.5-turbo",
        prompts={},
        split_correction=False,
    )

    success = convo.set_api_key(
        api_key="fake_key",
        user="test_user",
    )

    assert not success

def test_azure_raises_request_error():
    convo = AzureGptConversation(
        model_name="gpt-35-turbo",
        deployment_name="test_deployment",
        prompts={},
        split_correction=False,
        version="2023-03-15-preview",
        base_url="https://api.openai.com",
    )

    with pytest.raises(NotFoundError):
        convo.set_api_key("fake_key")

@patch("biochatter.llm_connect.AzureChatOpenAI")
def test_azure(mock_azurechat):
    """
    Test OpenAI Azure endpoint functionality. Azure connectivity is enabled by
    setting the corresponding environment variables.
    """
    # mock_azurechat.return_value.generate = 
    openai.proxy = os.getenv("AZURE_TEST_OPENAI_PROXY")
    convo = AzureGptConversation(
        model_name=os.getenv("AZURE_TEST_OPENAI_MODEL_NAME"),
        deployment_name=os.getenv("AZURE_TEST_OPENAI_DEPLOYMENT_NAME"),
        prompts={},
        split_correction=False,
        version=os.getenv("AZURE_TEST_OPENAI_API_VERSION"),
        base_url=os.getenv("AZURE_TEST_OPENAI_API_BASE"),
    )

    assert convo.set_api_key(os.getenv("AZURE_TEST_OPENAI_API_KEY"))

def test_xinference_init():
    """
    Test generic LLM connectivity via the Xinference client. Currently depends
    on a test server.
    """
    base_url = os.getenv("XINFERENCE_BASE_URL", "http://llm.biocypher.org")
    convo = XinferenceConversation(
        base_url=base_url,
        prompts={},
        split_correction=False,
    )
    assert convo.set_api_key()


# TODO move to test_chatting.py once exists
def test_generic_chatting():
    base_url = os.getenv("XINFERENCE_BASE_URL", "http://llm.biocypher.org")
    convo = XinferenceConversation(
        base_url=base_url,
        prompts={},
        correct=False,
    )
    (msg, token_usage, correction) = convo.query("Hello, world!")
    assert token_usage["completion_tokens"] > 0
