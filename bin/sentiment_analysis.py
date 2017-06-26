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
 
    def get_tweets(self, query, count = 10):
        '''
        Main function to fetch tweets and parse them.
        '''
        # empty list to store parsed tweets
        tweets = []
 
        try:
            # call twitter api to fetch tweets
            fetched_tweets = self.api.search(q = query, count = count)
 
            # parsing tweets one by one
            for tweet in fetched_tweets:
                # empty dictionary to store required params of a tweet
                parsed_tweet = {}
 
                # saving text of tweet
                parsed_tweet['text'] = tweet.text
                # saving sentiment of tweet
                parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)
 
                # appending parsed tweet to tweets list
                if tweet.retweet_count > 0:
                    # if tweet has retweets, ensure that it is appended only once
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
                else:
                    tweets.append(parsed_tweet)
 
            # return parsed tweets
            return tweets
 
        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))
 
if __name__ == "__main__":
    # creating object of TwitterClient Class
    api = TwitterClient()
    trending = ['$' + str(ticker) for ticker in stc.get_trending_stocks()]
    top_stock = ('',0)

    for ticker in trending:
        # calling function to get tweets
        tweets = api.get_tweets(query = ticker, count = 200)

        # picking positive tweets from tweets
        ptweets = [tweet for tweet in tweets if tweet['sentiment'] == 'positive']
        
        print('-----' + ticker.upper() + '-----')
        # percentage of positive tweets
        positive_tweets = 100*len(ptweets)/len(tweets)
        print("Positive tweets percentage: {} %".format(positive_tweets))

        if positive_tweets > top_stock[1]:
            top_stock = (ticker, positive_tweets)

        # picking negative tweets from tweets
        ntweets = [tweet for tweet in tweets if tweet['sentiment'] == 'negative']

        # percentage of negative tweets
        print("Negative tweets percentage: {} %".format(100*len(ntweets)/len(tweets)))

        # percentage of neutral tweets
        print("Neutral tweets percentage: {} % \
        ".format(100*(len(tweets) - len(ntweets) - len(ptweets))/len(tweets)))

    
    print('\nTop stock %s has the highest tweet percentage %d%%' % (top_stock[0],top_stock[1]))
    """
    # printing first 9 positive tweets
    print("\n\nPositive tweets:")
    for tweet in ptweets[:10]:
        print(tweet['text'])
 
    # printing first 9 negative tweets
    print("\n\nNegative tweets:")
    for tweet in ntweets[:10]:
        print(tweet['text'])
    """


        
        
