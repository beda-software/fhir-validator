#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import os
import zulip

from bot.settings import Settings

settings = Settings()

client = zulip.Client(email=settings.EMAIL, api_key=settings.API_KEY, site=settings.SITE)


def handle(message):
    if message["content"] == f"@**{settings.BOT_NAME}**":
        response = client.get_messages(
            {
                "anchor": message["id"],
                "num_before": 1,
                "num_after": 0,
                "apply_markdown": False,
            }
        )
        if response["result"] == "success":
            prev_message = response["messages"][0]["content"]
            if prev_message.startswith("```"):
                prev_message = prev_message[3:-3]
            data = json.loads(prev_message)
            resource = data["resourceType"]
            r = requests.post(
                f"https://validator.aidbox.app/fhir/{resource}/$validate",
                headers={"authorization": settings.AUTHORIZATION,},
                json=data,
            )
            if r.status_code == 200:
                validation_response = r.json()
                message_data = {
                    "type": message["type"],
                    "content": f"```\n{json.dumps(validation_response, indent=2)}\n```",
                    "subject": message["subject"],
                    "to": [message["display_recipient"]],
                }
                client.send_message(message_data)

client.call_on_each_message(handle)
