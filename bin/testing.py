#!/usr/bin/env python
#Import the necessary methods from tweepy library
import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import pandas as pd
import re
import stocktwits.api as stc
from textblob import TextBlob
import time 
import Queue
import signal
import sys
from threading import Thread

#disable unsecure warning
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

stock_tweets = {}
trending = []
api = None
flag = 1
DEBUG = 1

def signal_handler(signal, frame):
    global flag
    flag = 0
    sys.exit(0)

class TwitterClient(object):

    def __init__(self):
        #Variables that contains the user credentials to access Twitter API 

        access_token = "1518310573-wZ4sDaFpEUXjSev2QMxl4WW4WN4fzl94qGm7UF9"
        access_token_secret = "esP6wEjyEzYBQdhWxls0tIFB0DFc25zOyy98Kb27No19e"
        consumer_key = "M9Z2tc3gY05m9a67IsfAGEdQp"
        consumer_secret = "DRcVhwFzMAFK7ZRKFVuPE8o4SIRrMiLWRRvFWJu4x5wcD5IKoM"

        try:
            # create OAuthHandler object
            self.auth = OAuthHandler(consumer_key, consumer_secret)
            # set access token and secret
            self.auth.set_access_token(access_token, access_token_secret)
            # create tweepy API object to fetch tweets
            self.api = tweepy.API(self.auth)
        except:
            print("Error: Authentication Failed!")
    
    def clean_tweet(self, tweet):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        '''
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
 
    def get_tweet_sentiment(self, tweet):
        '''
        Utility function to classify sentiment of passed tweet
        using textblob's sentiment method
        '''
        # create TextBlob object of passed tweet text
        analysis = TextBlob(self.clean_tweet(tweet))
        # set sentiment
        if analysis.sentiment.polarity > 0:
            return 'positive'
        elif analysis.sentiment.polarity == 0:
            return 'neutral'
        else:
            return 'negative'
 
    def get_tweets(self, query, count = 30):
        global stock_tweets

        '''
        Main function to fetch tweets and parse them.
        '''
        try:
            # call twitter api to fetch tweets
            fetched_tweets = self.api.search(q = query, count = count)
 
            # parsing tweets one by one
            for tweet in fetched_tweets:
                tweet_sent = self.get_tweet_sentiment(tweet.text)
                
                tweet = json.loads(json.dumps(tweet._json))

                if 'FAST' in tweet['text']:
                    print('------------------')
                    print(tweet['text'])
                    print(tweet_sent)
                #TODO: In future check if tweet is already in queue
                # because retweets are possible
                if stock_tweets[query].full():
                    stock_tweets[query].get()
                stock_tweets[query].put((tweet['created_at'], tweet_sent == 'positive'))
        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))

class StdOutListner(StreamListener):
    def on_data(self, data):
        global stock_tweets
        global trending

        # Check what ticker symbol the data is about and push to queue
        tweet = json.loads(data)
        ticker = ''
        
        for stock in trending:
            if stock in tweet['text']:
                if stock_tweets[stock].full():
                    stock_tweets[stock].get()
                stock_tweets[stock].put((tweet['created_at'], api.get_tweet_sentiment(tweet['text']) == 'positive' ))
        return True

        def on_error(self, status):
            print status
            
def data_processing(): 
    global flag
    while(flag):
        top_stock = ('',0)
        for stock in trending:
            queue_arr = list(stock_tweets[stock].queue)
            count = 0

            for data in queue_arr:
                sentiment = data[1]
                if sentiment:
                    count += 1
                
            positive_sentiment = 100*count/len(queue_arr)
            if positive_sentiment > top_stock[1]:
                top_stock = (stock,positive_sentiment)

        print('Top Stock:%s %d%%' % (top_stock[0], top_stock[1]))
        time.sleep(5)

if __name__ == "__main__":
    # creating object of TwitterClient Class
    signal.signal(signal.SIGINT, signal_handler)
    api = TwitterClient()
    l = StdOutListner()
    
    thread = Thread(target = data_processing)

    trending = ['$' + str(ticker) for ticker in stc.get_trending_stocks()]
    stream = Stream(api.auth, l)

    for ticker in trending:
        if ticker not in stock_tweets:
            stock_tweets[ticker] = Queue.PriorityQueue(maxsize=30)            

        # calling function to get tweets
        api.get_tweets(query=ticker, count = 30)

    # Adjust filter to stop after 30 min to check if there are other trending threads
    thread.start()
    stream.filter(track=trending)
    


        
