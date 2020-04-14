import pytest

from bot import Bot
from stories import Success, Result, Failure, Skip
from unittest.mock import MagicMock, patch

BOT_NAME = "validator"
TOKEN = "Bearer token"


def make_context(ctx):
    return type("Context", (), ctx)


@pytest.fixture
def bot():
    client = MagicMock()
    return Bot(client, BOT_NAME, TOKEN)


def test_check_that_it_is_my_message_step(bot):
    ctx = make_context({"message": {"content": f"@**{BOT_NAME}**"}})
    assert isinstance(bot.check_that_it_is_my_message(ctx), Success)

    ctx = make_context({"message": {"content": "some text"}})
    assert isinstance(bot.check_that_it_is_my_message(ctx), Skip)


def test_load_previous_message_step():
    client = MagicMock()
    message_content = "hello world"
    client.get_messages = MagicMock(
        return_value={"result": "success", "messages": [{"content": message_content}]}
    )
    bot = Bot(client, BOT_NAME, TOKEN)

    ctx = make_context({"message": {"id": "123"}})
    assert isinstance(bot.load_previous_message(ctx), Success)
    client.get_messages.assert_called_once()
    assert ctx.prev_message == message_content

    client.get_messages = MagicMock(return_value={"result": "failure"})
    ctx = make_context({"message": {"id": "123"}})
    assert isinstance(bot.load_previous_message(ctx), Failure)
    client.get_messages.assert_called_once()


def test_parse_fhir_resource_step(bot):
    ctx = make_context({"prev_message": '{"resourceType": "Patient"}'})
    assert isinstance(bot.parse_fhir_resource(ctx), Success)
    assert ctx.resource == {"resourceType": "Patient"}

    ctx = make_context({"prev_message": '```\n{"resourceType": "Patient"}\n```'})
    assert isinstance(bot.parse_fhir_resource(ctx), Success)
    assert ctx.resource == {"resourceType": "Patient"}

    ctx = make_context({"prev_message": "some dummy text"})
    assert isinstance(bot.parse_fhir_resource(ctx), Failure)


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def test_validate_fhir_resource_step(bot):
    r = {"resourceType": "OperationOutcome", "id": "valid"}
    with patch("requests.post", return_value=MockResponse(r)) as request:
        ctx = make_context({"resource": {"resourceType": "Patient"}})
        assert isinstance(bot.validate_fhir_resource(ctx), Success)
        assert ctx.validation_response == r
        request.assert_called_once()

    with patch("requests.post", return_value=MockResponse(r)) as request:
        ctx = make_context({"resource": {"id": "id"}})
        assert isinstance(bot.validate_fhir_resource(ctx), Failure)

    with patch("requests.post", return_value=MockResponse(r, 400)) as request:
        ctx = make_context({"resource": {"id": "id"}})
        assert isinstance(bot.validate_fhir_resource(ctx), Failure)


def test_send_validation_response_step():
    client = MagicMock()
    response = {"result": "success"}
    client.send_message = MagicMock(return_value=response)
    bot = Bot(client, BOT_NAME, TOKEN)

    r = {"resourceType": "OperationOutcome", "id": "valid"}
    ctx = make_context(
        {
            "validation_response": r,
            "message": {
                "type": "stream",
                "subject": "SubjectName",
                "display_recipient": "r",
            },
        }
    )
    assert isinstance(bot.send_validation_response(ctx), Result)
