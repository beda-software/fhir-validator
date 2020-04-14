import json
import logging
import requests

from stories import story, arguments, Success, Result, Failure, Skip

logger = logging.getLogger("bot")


class Bot:
    def __init__(self, client, bot_name, authorization):
        self._client = client
        self._bot_name = bot_name
        self._authorization = authorization

    @classmethod
    def run(cls, *args):
        instance = cls(*args)

        def _handle(message):
            result = instance.handle.run(message=message)
            if result.is_failure:
                logger.warning("%s", result.ctx)

        return _handle

    @story
    @arguments("message")
    def handle(I):
        I.check_that_it_is_my_message
        I.load_previous_message
        I.parse_fhir_resource
        I.validate_fhir_resource
        I.send_validation_response

    def check_that_it_is_my_message(self, ctx):
        if ctx.message["content"] == f"@**{self._bot_name}**":
            return Success()
        else:
            return Skip()

    def load_previous_message(self, ctx):
        response = self._client.get_messages(
            {
                "anchor": ctx.message["id"],
                "num_before": 1,
                "num_after": 0,
                "apply_markdown": False,
            }
        )
        if response["result"] == "success" and len(response["messages"]) > 1:
            ctx.prev_message = response["messages"][0]["content"]
            return Success()
        else:
            return Failure()

    def parse_fhir_resource(self, ctx):
        try:
            prev_message = ctx.prev_message
            if prev_message.startswith("```"):
                prev_message = prev_message[3:-3]
            ctx.resource = json.loads(prev_message)
            return Success()
        except Exception as err:
            ctx.err = err
            return Failure()

    def validate_fhir_resource(self, ctx):
        resource_type = ctx.resource["resourceType"]
        r = requests.post(
            f"https://validator.aidbox.app/fhir/{resource_type}/$validate",
            headers={"authorization": self._authorization,},
            json=ctx.resource,
        )
        if r.status_code == 200:
            ctx.validation_response = r.json()
            return Success()
        else:
            return Failure()

    def send_validation_response(self, ctx):
        formated_response = json.dumps(ctx.validation_response, indent=2)
        message_data = {
            "type": ctx.message["type"],
            "content": f"```\n{formated_response}\n```",
            "subject": ctx.message["subject"],
            "to": [ctx.message["display_recipient"]],
        }
        return Result(
            {"validated": True, "response": self._client.send_message(message_data)}
        )
