import sys
sys.path.append('C:/Users/William/Documents/GitHub/faber-trading-strategy/algos')
from numpy import mean
from collections import defaultdict
from zipline.api import order, order_target, record, symbol, date_rules, time_rules, schedule_function
from write_to_sql import run
import pandas as pd
import os

from zipline.finance import commission

def initialize(context):
    """
    Stores the names of the stocks we'll be looking at.
    
    Input: a persistent namespace where we store an SID/list of SIDs
    
    Output: n/a
    """
    context.benchmark = symbol('SPY')

    context.symbol = [symbol('XLB'),
                      symbol('XLE'),
                      symbol('XLF'), 
                      symbol('XLK'), 
                      symbol('XLP'), 
                      symbol('XLY')]

    # skip the first 300 days of the timeframe so that we have enough data to calculate our 10 month SMA
    context.skip = 0
    context.init = True

    # keep track of number of shares bought
    context.shares = defaultdict(int)
    context.moving_avg = defaultdict(int)
    context.monthly_price = defaultdict(list)  

    context.set_commission(commission.PerShare(cost=0))

    # skip the first 10 months so that we have enough data to establish our moving average    
    schedule_function(buy_monthly, date_rules.month_end(days_offset=0), time_rules.market_close(minutes=2))

def handle_data(context, data):
    """
    Calls the trading strategy function at the end of every month.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing)
    """
    # context.portfolio.starting_cash = float(100000)
    pass

def buy_monthly(context, data):
    """
    Herein lies Faber's trading strategy.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing) on the last trading day of each month
    """

    context.skip += 1
    value = context.portfolio.portfolio_value

    # reevaluate portfolio
    context.positions = 0
    for asset in context.symbol:
        context.positions += context.shares[asset] * data.current(asset, 'close')

    if context.skip < 10:
        for asset in context.symbol:
            price = data.current(asset, 'close')
            context.monthly_price[asset].append(price)

    else:
        # record benchmark's "first" price
        if context.init == True:
            context.ratio = context.portfolio.portfolio_value / data.current(context.benchmark, 'close')
            context.init = False

        for asset in context.symbol:
            price = data.current(asset, 'close')

            # Get closing price on last trading day of month
            context.monthly_price[asset].append(price)

            if context.skip > 10:
                del context.monthly_price[asset][0]

            # calculate the 10-month moving average of each asset
            context.moving_avg[asset] = mean(context.monthly_price[asset])
        
        ### Faber's trading strategy ###
        
        # if the current price exceeds moving average and we haven't already bought any shares, buy
        for asset in context.symbol:
            # the most current monthly price will be the one added most recently (so it'll be the element on the end of the list)
            if context.monthly_price[asset][-1] >= context.moving_avg[asset]:
                # order_target(asset, 50, limit_price=data.current(asset, 'price'))
                order_target(asset, 500)
                context.shares[asset] = 500

            # else if the current price is below moving average and we have 500 shares of the asset, sell
            elif context.monthly_price[asset][-1] < context.moving_avg[asset]:
                order_target(asset, 0)
                context.shares[asset] = 0

        # # record portfolio value
        # record(portfolio = context.portfolio.portfolio_value)

        # # record returns
        # record(returns = context.portfolio.returns)

        # # also record the S&P 500 monthly price
        # record(SPY = context.ratio * data.current(context.benchmark, 'close'))
     
def analyze(context = None, results = None):
    """
    Plots the results of the strategy against a buy-and-hold strategy.
    
    Input: n/a?
    
    Output: a plot of two superimposed curves, one being Faber's strategy and the other being a buy-and-hold strategy.
    """
    # import matplotlib.pyplot as plt

    # txn = results['transactions']
    # txn.to_csv('transactions.csv')

    # fig = plt.figure()
    # ax1 = fig.add_subplot(211)

    # # plot both the portfolio based on faber's strategy and a buy-and-hold strategy
    # results['portfolio'].plot(ax=ax1)
    # results['SPY'].plot(ax=ax1)
    # ax1.set_ylabel('Portfolio value (USD)')

    # ax2 = fig.add_subplot(212)
    # results['returns'].plot(ax=ax2)
    # ax2.set_ylabel('Cumulative Returns')

    # results['SPY'].to_csv('benchmark.csv')
   
    # # export portfolio values to csv file
    # results['returns'].to_csv('zipline_returns.csv')

    # plt.show()


    import pyfolio as pf

    returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(results)

    pf.create_full_tear_sheet(returns, positions=positions, transactions=transactions)

    # tickers = []
    # for symbol in context.symbol:
    #     symbol = str(symbol).translate(None, '0123456789[]() ')[6:]
    #     tickers.append(symbol)

    # run('test.db', results, 'faber', tickers)
