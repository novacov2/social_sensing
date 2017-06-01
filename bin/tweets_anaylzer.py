#!/bin/env python
import json
import pandas as pd
import matplotlib.pyplot as plt
import re

tweets_data_path = '../data/twitter_data.txt'
tweets_data = []
tweets_file = open(tweets_data_path, "r")

for line in tweets_file:
    try:
        tweet = json.loads(line)
        if 'text' in tweet:
            tweets_data.append(tweet)
    except:
        continue

print "The number of trump tweets are %d" % len(tweets_data)

def extract_link(text):
    regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    match = re.search(regex, text)
    if match:
        return match.group()
    return ''

def word_in_text(word, text):
    word = word.lower()
    text = text.lower()
    match = re.search(word, text)
    if match:
        return True
    return False

# createt data frame 
tweets = pd.DataFrame()
tweets['text'] = map(lambda tweet: tweet.get('text', None),tweets_data)
tweets['lang'] = map(lambda tweet: tweet.get('lang',None), tweets_data)
tweets['country'] = map(lambda tweet: tweet['place']['country'] if tweet['place'] != None else None, tweets_data)
tweets['trump'] = tweets['text'].apply(lambda tweet: word_in_text('trump', tweet))
tweets['link'] = tweets['text'].apply(lambda tweet: extract_link(tweet))

print tweets['link']

