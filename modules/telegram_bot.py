#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Simple Bot to send timed Telegram messages.
# This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot and the JobQueue to send
timed messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram.ext import Updater

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hi!')


def send_message(bot, job):
    """Send the message."""
    bot.send_message(job.context, text='Beep!')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main(token):
    """Run bot."""
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    send_message("Hola")
    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    # updater.idle()


if __name__ == '__main__':
    TOKEN = "691918800:AAH8ZbKRsvOWQDUc0tIKO723wCFqUPK8neo"
    CHAT_ID = "58293600"
    main()
