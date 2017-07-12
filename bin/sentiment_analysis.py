#Import the necessary methods from tweepy library
import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import pandas as pd
import matplotlib.pyplot as plt
import re
import stocktwits.api as stc
from textblob import TextBlob
import ib_api as ibapi
from ib.opt import Connection
from datetime import datetime, time
import time
import Queue
import signal
import sys
from threading import Thread
from stocksim import StockSim

#disable unsecure warning
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

#global variables
current_stock = ['', 0]
stock_tweets = {}
trending = []
api = None
flag = 1
sim = None
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
                #TODO: In future check if tweet is already in queue
                # because retweets are possible
                if stock_tweets[query].full():
                    stock_tweets[query].get()
                stock_tweets[query].put((tweet['created_at'], tweet_sent == 'positive'))
        except tweepy.TweepError as e:
            print("Error : " + str(e))
 
        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))


def print_closed_banner():
    print('|-----------------------------------------------------|')
    print('|                                                     |')
    print('|               Market is now closed                  |')
    print('|                                                     |')
    print('|-----------------------------------------------------|')
    

class StdOutListener(StreamListener):
    def on_data(self, data):
        global stock_tweets
        global trending

        try:
            # Check what ticker symbol the data is about and push to queue
            tweet = json.loads(data)

            for stock in trending:
                if stock in tweet['text']:
                    if stock_tweets['$' + stock].full():
                        stock_tweets['$' + stock].get()
                    #TODO: Check if tweet is already in queue
                    if DEBUG == 1:
                        print('-----------------------')
                        print(tweet['text'])
                        print(api.get_tweet_sentiment(tweet['text']))
                    stock_tweets['$' + stock].put((tweet['created_at'], api.get_tweet_sentiment(tweet['text']) == 'positive' ))
        except KeyError as k:
            print(k)
        

        return True

        def on_error(self, status):
            with open('listener.log', 'w') as f:
                f.write(status)
            

def QueueSentiment(q):
    queue_arr = list(q.queue)
    count = 0
    for data in queue_arr:
        sentiment = data[1]
        if sentiment:
            count += 1
    return 100*count/len(queue_arr)

def data_processing(): 
    global flag
    global current_stock

    while(flag):
        top_stock = ('',0)
        for stock in trending:
            positive_sentiment = QueueSentiment(stock_tweets['$' + stock])

            if positive_sentiment >= top_stock[1]:
                top_stock = (stock,positive_sentiment)

        #Check if current stock should be sold
        if current_stock[0] != '':        
            if top_stock[0] != current_stock[0] and top_stock[1] >= QueueSentiment(stock_tweets['$' + current_stock[0]]):
                print('Selling 100 shares of %s' % current_stock[0])
                sim.sell_stock(top_stock[0])

                price = sim.stock_price(top_stock[0])
                bpwr = sim.buying_pwr()
                shares = int(bpwr*.8/price)
                print('Buying %d shares of %s' % (shares,top_stock[0]))
                sim.buy_stock(top_stock[0], shares)
                current_stock = (top_stock[0], top_stock[1])

        else:
            price = sim.stock_price(top_stock[0])
            bpwr = sim.buying_pwr()
            shares = int(bpwr*.8/price)
            print('Buying %d shares of %s' % (shares,top_stock[0]))
            sim.buy_stock(top_stock[0], shares)
            current_stock = (top_stock[0], top_stock[1])


        print('Top Stock:%s %d%%' % (top_stock[0], top_stock[1]))
        print('Account Balalnce: %f' % sim.acc_bal())
        print('Percentage Gain: %f%%' % (100*(sim.acc_bal() - 100000)/100000) )
        time.sleep(5)

if __name__ == "__main__":
    # Make sure program exits on signal interrupt
    signal.signal(signal.SIGINT, signal_handler)

    # Create listener for stream
    l = StdOutListener()

    # creating object of TwitterClient Class
    api = TwitterClient()

    # Create object for stock market simulation
    sim = StockSim()

    #while(datetime.now().time() >= time(7,30) and datetime.now().time() <= time(13,0)):
    thread = Thread(target=data_processing)
    stream = Stream(api.auth, l)

    trending = [str(ticker) for ticker in stc.get_trending_stocks()]


    for ticker in trending:
        if ticker not in stock_tweets:
            stock_tweets['$' + ticker] = Queue.PriorityQueue(maxsize=30)

        # calling function to get tweets
        api.get_tweets(query = '$' + ticker, count = 30)

    thread.start()
    stream.filter(track=['$' + stock for stock in trending])

