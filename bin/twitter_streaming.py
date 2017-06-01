#Import the necessary methods from tweepy library
import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import pandas as pd
import matplotlib.pyplot as plt

#Variables that contains the user credentials to access Twitter API 
access_token = "1518310573-wZ4sDaFpEUXjSev2QMxl4WW4WN4fzl94qGm7UF9"
access_token_secret = "esP6wEjyEzYBQdhWxls0tIFB0DFc25zOyy98Kb27No19e"
consumer_key = "M9Z2tc3gY05m9a67IsfAGEdQp"
consumer_secret = "DRcVhwFzMAFK7ZRKFVuPE8o4SIRrMiLWRRvFWJu4x5wcD5IKoM"


#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def on_data(self, data):
        print data
        return True

    def on_error(self, status):
        print status


if __name__ == '__main__':

    #This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)
    api = tweepy.API(auth)

    #This line filter Twitter Streams to capture data by the keywords: 'python', 'javascript', 'ruby'
    #stream.filter(track=['trump'])

# print all tweets about trump
    for tweet in tweepy.Cursor(api.search, q='$AMD').items(10):
        print "----------------------------------"
        print(tweet.text)
        print("@" + tweet.user.screen_name)
        print(tweet.created_at)
        print "----------------------------------"


