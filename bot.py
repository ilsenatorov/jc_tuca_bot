#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Bot for parsing the articles. Parse the token into the start_bot function or with -t if launching as script.
'''
import argparse
import logging
import re
from urllib import request

import pandas as pd

import telegram
from bs4 import BeautifulSoup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, Filters, RegexHandler, Updater

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

### BOT COMMANDS ###


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

def remove_tag(text):
    '''
    Remove the hashtag from the text
    '''
    return re.sub('#статья146', '', text).strip()

def remove_link(text):
    '''
    Remove the links from the text
    '''
    return re.sub("(?P<url>https?://[^\s]+)", '', text).strip()

def find_link(text):
    '''
    Extracts the link from the text
    '''
    return re.search("(?P<url>https?://[^\s]+)", text).group("url")

def parse_paper(update, context):
    '''
    This is called when a message that contains info about the article is sent
    '''
    df = pd.read_csv('papers.tsv', index_col=0, sep='\t')
    txt = update.message.text
    url = find_link(txt)
    html = request.urlopen(url).read().decode('utf8')
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title').string
    df = df.append({'link':url, 'title':title}, ignore_index=True)
    df.to_csv('papers.tsv', sep='\t')
    update.message.reply_text('Added')

def get_poll_options(df):
    '''
    Given the dataframe of the articles, create all the poll options.
    Note the limit on message length of 100 symbols
    '''
    return [x for x in df.title.apply(lambda x: x if len(x) < 99 else x[:97] + '...')]

def get_info(df):
    '''
    Compile a message with info about the articles
    '''
    return '\n\n####################\n\n'.join([x for x in (df['title'] + '\n\n' + df['link'])])

def poll(update, context):
    '''
    Used when /poll is called
    '''
    df = pd.read_csv('papers.tsv', sep='\t')
    if not df.empty:
        update.message.reply_poll(question='Papers for next week',
                            options=get_poll_options(df),
                            is_anonymous=True,
                            allows_multiple_answers=True)
    else:
        update.message.reply_text('No papers in the log currently')

def clear(update, context):
    '''
    Clears the dataframe
    '''
    df = pd.DataFrame(columns=['index', 'link', 'title']).to_csv('papers.tsv', sep='\t')
    update.message.reply_text('Cleared the papers')

def info(update, context):
    '''
    Called when /info is called
    '''
    df = pd.read_csv('papers.tsv', index_col=0, sep='\t')
    if not df.empty:
        update.message.reply_text(get_info(df),
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




def start_bot(token):
    '''
    The main runner function, starts the bot and keeps it running
    '''
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
    start_bot(token=args.t)
