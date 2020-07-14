#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
The Degenerate Bot, Zhenya. Parse the token into the start_zhenya function or with -q if launching as script.
'''
import argparse
import logging

from urllib import request
from bs4 import BeautifulSoup

import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, Filters,
                          RegexHandler, Updater)

import pandas as pd
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

### BOT COMMANDS ###

CHOOSING, RMGROUP, ADDGROUP, RMFROMGROUP = range(4)



def start(update, context):
    '''
    Define the /start command
    '''
    update.message.reply_text(text="""This is a bot for creating polls in JC TUCA

Available commands:
/poll - Post the poll to the current chat
/info - Post the descriptions of all the papers
/clear - Clear the papers
""")

def get_options(df):
    # df = pd.read_csv('papers.tsv', sep='\t')
    return df['title'].to_list()

def remove_tag(text):
    return re.sub('#статья146', '', text).strip()

def remove_link(text):
    return re.sub("(?P<url>https?://[^\s]+)", '', text).strip()

def find_link(text):
    return re.search("(?P<url>https?://[^\s]+)", text).group("url")

def parse_paper(update, context):
    df = pd.read_csv('papers.tsv', index_col=0, sep='\t')
    txt = remove_tag(update.message.text).encode('utf-8')
    url = find_link(txt)
    html = request.urlopen(url).read().decode('utf8')
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title').string
    df = df.append({'message':txt,'link':url, 'title':title, 'description':remove_link(txt)}, ignore_index=True)
    df.to_csv('papers.tsv', sep='\t')
    update.message.reply_text('Added')

def poll(update, context):
    df = pd.read_csv('papers.tsv', sep='\t')
    if not df.empty:
        update.message.reply_poll(question='Papers for next week',
                            options=df['title'].to_list(),
                            is_anonymous=True,
                            allows_multiple_answers=True)
    else:
        update.message.reply_text('No papers in the log currently')

def clear(update, context):
    df = pd.DataFrame(columns=['index', 'message', 'link', 'title', 'description']).to_csv('papers.tsv', sep='\t')
    update.message.reply_text('Cleared the papers')

def info(update, context):
    df = pd.read_csv('papers.tsv', index_col=0, sep='\t')
    if not df.empty:
        update.message.reply_text('\n\n####################\n\n'.join((df['title'] + '\n\n' + df['link']).to_list()),
                                disable_web_page_preview=True)
    else:
        update.message.reply_text('No papers in the log currently')

def error(update, context):
    '''
    Print warnings in case of errors
    '''
    logger.warning('Update "%s" caused error "%s"',
                    update,
                    context.error)




def start_zhenya(token):
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    # Add all the handlers
    dispatcher.add_handler(RegexHandler('#статья146', parse_paper))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('poll', poll))
    dispatcher.add_handler(CommandHandler('clear', clear))
    dispatcher.add_handler(CommandHandler('info', info))
    dispatcher.add_error_handler(error)


    # Start the bot
    updater.start_polling()
    # idle is better than just polling, because of Ctrl+c
    updater.idle()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-t", help="your bot API token", type=str)
    args = parser.parse_args()
    start_zhenya(token=args.t)
