from googlefinance import getQuotes
import json
import time

class StockSim(object):
    def __init__(self, acc_bal = 100000):
        self.bpwr = acc_bal
        self.portfolio = {}

    def buying_pwr(self):
        return self.bpwr
        
    def acc_bal(self):
        count = self.bpwr
        for stock, shares in self.portfolio.items():
            stock_info = getQuotes(stock)[0]
            price = float(stock_info['LastTradePrice'])
            count += price * shares
        return count

    def stock_price(self, ticker):
        return float(getQuotes(ticker)[0]['LastTradePrice'])

    # Ticker must have no '$' sign
    def buy_stock(self, ticker, shares = 100):
        stock = getQuotes(ticker)[0]
        price = float(stock['LastTradePrice'])
        
        if (price * shares <= self.bpwr):
            self.bpwr -= price * shares
        else:
            'TODO: raise error not enough funds'

        if ticker in self.portfolio:
            self.portfolio[ticker] += shares
        else:
            self.portfolio[ticker] = shares

    def sell_stock(self, ticker, shares=100):
        stock = getQuotes(ticker)[0]
        price = float(stock['LastTradePrice'])

        if ticker not in self.portfolio:
            'TODO: raise error do not have this stock'

        if (shares <= self.portfolio[ticker]):
            self.bpwr += price * shares
            self.portfolio[ticker] -= shares
        else:
            'TODO: raise error do not have amount of shares'


