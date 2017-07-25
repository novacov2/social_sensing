#Import the necessary methods from tweepy library
import tweepy
import os
import json
import re
import stocktwits.api as stc
# must name something other than time because conflicts with datetime
import time as t
import Queue
import signal
import requests
import sys
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from datetime import datetime, time
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
log = None 
data = None

log_path  = os.path.dirname(os.path.abspath(__file__)) + '/../logs/log.txt'
data_path = os.path.dirname(os.path.abspath(__file__)) + '/../data/data%s.txt' % datetime.today().strftime('%m-%d-%Y')

def print_to_log(text):
    global log
    log.write(text + '\n')

def print_to_data(text):
    global data
    data.write(text + '\n')

def signal_handler(signal, frame):
    global flag
    flag = 0
    


def create_sim():
    global sim

    dp = os.path.dirname(os.path.abspath(__file__)) + '/../data/current_info'
    if os.path.exists(dp):
        with open(dp, 'r') as f:
            last = f.readline()
            sim = StockSim(float(last))
    else:
        sim = StockSim()
            

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
            if DEBUG:
                print("Error: Authentication Failed!")
            print_to_log("Error: Authentication Failed!")
    
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
                stock_tweets[query].put((tweet['created_at'], tweet_sent == 'positive', tweet['text']))
        except tweepy.TweepError as e:
            if DEBUG:
                print("Error : " + str(e))
            print_to_log("Error : " + str(e))
 
        except tweepy.TweepError as e:
            # print error (if any)
            if DEBUG:
                print("Error : " + str(e))
            print_to_log("Error : " + str(e))


def print_closed_banner():
    if DEBUG:
        print('|-----------------------------------------------------|')
        print('|                                                     |')
        print('|               Market is now closed                  |')
        print('|                                                     |')
        print('|-----------------------------------------------------|')
    print_to_log('|-----------------------------------------------------|')
    print_to_log('|                                                     |')
    print_to_log('|               Market is now closed                  |')
    print_to_log('|                                                     |')
    print_to_log('|-----------------------------------------------------|')
    

def isDup(q, text):
    queue_arr = list(q.queue)
    for data in queue_arr:
        if data == text:
            return True
    return False

class StdOutListener(StreamListener):
    def on_data(self, data):
        global stock_tweets
        global trending
        global flag

        if(datetime.now().time() >= time(9,30) and datetime.now().time() <= time(16,0)):
            # Check what ticker symbol the data is about and push to queue
            tweet = json.loads(data)

            for stock in trending:
                if stock in tweet['text']:
                    #TODO: starting push text into queue to see if there are retweets/ spammers of a stock                                        
                    if isDup(stock_tweets['$' + stock], tweet['text']):
                        continue

                    if stock_tweets['$' + stock].full():
                        stock_tweets['$' + stock].get()

                    if DEBUG == 1:
                        print('-----------------------')
                        print(tweet['text'])
                        print(api.get_tweet_sentiment(tweet['text']))
                        print_to_log('-----------------------')
                        print_to_log(tweet['text'])
                        print_to_log(api.get_tweet_sentiment(tweet['text']))

                    stock_tweets['$' + stock].put((tweet['created_at'], api.get_tweet_sentiment(tweet['text']) == 'positive' , tweet['text']))
            return True
        else:
            flag = 0
            return False

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

def get_stock_twits_data():
    global trending
    while(flag):
        messages = stc.get_stock_streams(trending)['messages']
        for stock in trending:
            for message in messages:
                """ TODO: CHECK IF DUP EXISTS """
                if stock_tweets['$' + stock].full():
                    stock_tweets['$' + stock].get()

                stock_tweets['$' + stock].put((message['created_at'], api.get_tweet_sentiment(message['body']) == 'positive', message['body']))
        # Rate limit is 400 requests per hour = 1/9 requests per second
        t.sleep(10)

def data_processing(): 
    global flag
    global current_stock

    count = 0
    while(flag):
        if(not (datetime.now().time() >= time(9,30) and datetime.now().time() <= time(16,0))):
            flag = 0 
            break;

        top_stock = ('',0)
        for stock in trending:
            positive_sentiment = QueueSentiment(stock_tweets['$' + stock])

            if positive_sentiment >= top_stock[1]:
                top_stock = (stock,positive_sentiment)

        #Check if current stock should be sold
        if current_stock[0] != '':        
            if top_stock[0] != current_stock[0] and top_stock[1] >= QueueSentiment(stock_tweets['$' + current_stock[0]]):
                if DEBUG:
                    print('Selling %d shares of %s' % (sim.get_shares(current_stock[0]), current_stock[0]))
                print_to_log('Selling %d shares of %s' % (sim.get_shares(current_stock[0]), current_stock[0]))
                
                sim.sell_stock(current_stock[0], sim.get_shares(current_stock[0]))

                price = sim.stock_price(top_stock[0])
                bpwr = sim.buying_pwr()
                shares = int(bpwr*.8/price)

                if DEBUG:
                    print('Buying %d shares of %s' % (shares,top_stock[0]))
                print_to_log('Buying %d shares of %s' % (shares,top_stock[0]))

                sim.buy_stock(top_stock[0], shares)
                current_stock = (top_stock[0], top_stock[1])

        else:
            price = sim.stock_price(top_stock[0])
            bpwr = sim.buying_pwr()
            shares = int(bpwr*.8/price)

            if DEBUG:
                print('Buying %d shares of %s' % (shares,top_stock[0]))
            print_to_log('Buying %d shares of %s' % (shares,top_stock[0]))

            sim.buy_stock(top_stock[0], shares)
            current_stock = (top_stock[0], top_stock[1])

        acc_bal = sim.acc_bal()
        if DEBUG:
            print('Top Stock:%s %d%%' % (top_stock[0], top_stock[1]))
            print('Account Balalnce: %f' % acc_bal)
            print('Percentage Gain: %f%%' % (100*(acc_bal - 100000)/100000) )
        print_to_log('Top Stock:%s %d%%' % (top_stock[0], top_stock[1]))
        print_to_log('Account Balalnce: %f' % acc_bal)
        print_to_log('Percentage Gain: %f%%' % (100*(acc_bal - 100000)/100000) )

        if (count % 60 == 0):
            now = datetime.now()
            print_to_data('%s:%s %f' % (now.hour, now.minute, acc_bal))
            count = 0

        t.sleep(5)
        count +=5

if __name__ == "__main__":
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
        
    #create log of statements
    log = open(log_path, 'w', 1)

    # create data file to keep track of data points on graph
    data = open(data_path,'w', 1)

    # redirect all stderr too path
    sys.stderr = log

    # Make sure program exits on signal interrupt
    signal.signal(signal.SIGINT, signal_handler)

    # Create listener for stream
    l = StdOutListener()

    # creating object of TwitterClient Class
    api = TwitterClient()

    # Create object for stock market simulation
    #sim = StockSim()
    create_sim()


    thread = Thread(target=data_processing)
    thread1 = Thread(target=get_stock_twits_data)
    
    trending = [str(ticker) for ticker in stc.get_trending_stocks()]


    for ticker in trending:
        if ticker not in stock_tweets:
            stock_tweets['$' + ticker] = Queue.PriorityQueue(maxsize=50)

        # calling function to get tweets
        api.get_tweets(query = '$' + ticker, count = 30)

    thread1.start()
    thread.start()
    while flag:
        try:
            stream = Stream(api.auth, l)
            stream.filter(track=['$' + stock for stock in trending])
        except KeyboardInterrupt:
            if DEBUG:
                print('Exiting program \n')
            print_to_log('Exiting program \n')
            raise
        except:
            if DEBUG:
                print("INCOMPLETE READ")
            print_to_log("INCOMPLETE READ")
            continue

    thread.join()

    # write acc balance to file
    dp = os.path.dirname(os.path.abspath(__file__)) + '/../data/current_info'
    with open(dp, 'w') as f:
        f.write(str(sim.acc_bal()))

    print_closed_banner()
