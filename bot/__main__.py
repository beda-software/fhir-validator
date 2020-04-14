#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import zulip

from bot import Bot
from bot.settings import Settings

settings = Settings()

client = zulip.Client(
    email=settings.EMAIL, api_key=settings.API_KEY, site=settings.SITE
)


if __name__ == "__main__":
    client.call_on_each_message(
        Bot.run(client, settings.BOT_NAME, settings.AUTHORIZATION)
    )
