# -*- coding: utf-8 -*-
from marvinbot.utils import get_message
from marvinbot.plugins import Plugin
from marvinbot.handlers import CommandHandler
from bs4 import BeautifulSoup
import logging

import requests
import xmltodict

log = logging.getLogger(__name__)


class GasPrices(Plugin):
    def __init__(self):
        super(GasPrices, self).__init__('gas_prices')

    def get_default_config(self):
        return {
            'short_name': self.name,
            'enabled': True,
            'base_url': 'https://mic.gob.do/combustibleRSS.xml'
        }

    def configure(self, config):
        self.config = config
        pass

    def setup_handlers(self, adapter):
        self.add_handler(CommandHandler('gas', self.on_gas, command_description='Fetch gas prices from mic.gob.do'))

    def setup_schedules(self, adapter):
        pass

    def fetch_gas_prices(self):
        url = self.config.get('base_url')
        response = requests.get(url)
        return response.text

    def parse_gas_prices(self, text):
        return xmltodict.parse(text)


    def on_gas(self, update, *args, **kwargs):
        message = get_message(update)
        fetched_response = self.fetch_gas_prices()
        data = self.parse_gas_prices(fetched_response)

        rss = data.get('rss', None)
        if rss is None:
            message.reply_text(text="❌ Invalid response.")
            log.error("No rss")
            return

        channel = rss.get('channel', None)
        if channel is None:
            message.reply_text(text="❌ Invalid response.")
            log.error("No channel")
            return

        item = channel.get('item', None)
        if item is None:
            message.reply_text(text="❌ Invalid response.")
            log.error("No item")
            return

        responses = []
        title = item.get('title', '').strip()
        responses.append("⛽ <b>{}</b>\n".format(title))
        last_update = item.get('pubDate','').strip()

        description = item.get('description', '').encode('iso-8859-1').decode('utf8')

        soup = BeautifulSoup(description, 'html.parser')

        try:
            for div in soup.select("div"):
                category, price = div.contents
                responses.append("💰 {}{}".format(category.string, price))
        except Exception as err:
            log.error("Parse error: {}".format(err))

        responses.append("\n📅 Actualizado el {}".format(last_update))
        message.reply_text(text="\n".join(responses), parse_mode='HTML')


