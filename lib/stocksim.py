from googlefinance import getQuotes
import json

class StockSim(object):
    def __init__(self, acc_bal = 100000):
        self.acc_bal = acc_bal
        self.portfolio = {}

    def check_balance(self):
        return self.acc_bal
        
    # Ticker must have no '$' sign
    def buy_stock(self, ticker, shares = 100):
        stock = getQuotes(ticker)[0]
        price = float(stock['LastTradePrice'])
        
        if (price * shares <= self.acc_bal):
            self.acc_bal -= price * shares
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
            self.acc_al += price * shares
            self.portfolio[ticker] -= shares
        else:
            'TODO: raise error do not have amount of shares'

