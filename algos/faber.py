import sys
sys.path.append('C:/Users/William/Documents/GitHub/faber-trading-strategy/algos')
from numpy import mean
from collections import defaultdict
from zipline.api import order, record, symbol, date_rules, time_rules, schedule_function
from write_to_sql import run
import pandas as pd
import os

def initialize(context):
    """
    Stores the names of the stocks we'll be looking at.
    
    Input: a persistent namespace where we store an SID/list of SIDs
    
    Output: n/a
    """
    # set initial cash to 1 mil
    context.portfolio.portfolio_value = float(1000000)
    context.portfolio.cash = float(1000000)
    context.portfolio.positions_value = float(0)

    context.benchmark = symbol('SPY')

    context.symbol = [symbol('XLB'),
                      symbol('XLE'),
                      symbol('XLF'), 
                      symbol('XLK'), 
                      symbol('XLP'), 
                      symbol('XLY')]

    # skip the first 300 days of the timeframe so that we have enough data to calculate our 10 month SMA
    context.skip = 0

    # keep track of number of shares bought
    context.shares = defaultdict(int)
    context.moving_avg = defaultdict(int)
    context.monthly_price = defaultdict(list)

    # keep track of how much one buys per monthly buying period
    context.money_spent = 0

    # skip the first 10 months so that we have enough data to establish our moving average    
    schedule_function(buy_monthly, date_rules.month_end(), time_rules.market_close())

def handle_data(context, data):
    """
    Calls the trading strategy function at the end of every month.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing)
    """
    pass

def buy_monthly(context, data):
    """
    Herein lies Faber's trading strategy.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing) on the last trading day of each month
    """

    context.skip += 1
    context.money_spent = 0

    if context.skip < 10:
        for asset in context.symbol:
            price = data.current(asset, 'price')
            context.monthly_price[asset].append(price)

    else:
        # record benchmark's "first" price
        if context.skip == 10:
            context.ratio = context.portfolio.portfolio_value / data.current(context.benchmark, 'price')

        for asset in context.symbol:
            price = data.current(asset, 'price')

            # Get closing price on last trading day of month
            context.monthly_price[asset].append(price)
            context.monthly_price[asset] = context.monthly_price[asset][1:11]

            # calculate the 10-month moving average of each asset
            context.moving_avg[asset] = mean(context.monthly_price[asset])

        
        ### Faber's trading strategy ###
        
        # if the current price exceeds moving average, long
        for asset in context.symbol:
            # the most current monthly price will be the one added most recently (so it'll be the element on the end of the list)
            # if context.monthly_price[asset][-1] > context.moving_avg[asset] and context.portfolio.cash > 0:
            if context.monthly_price[asset][-1] > context.moving_avg[asset] and context.money_spent < context.portfolio.portfolio_value:
                order(asset, 500)
                context.shares[asset] += 500

                # add amount ordered to total money spent during this specific buying period
                context.money_spent += 500 * data.current(asset, 'price')

                # change cash amount
                context.portfolio.cash -= 500 * data.current(asset, 'price')

                # change positions value
                context.portfolio.positions_value += 500 * data.current(asset, 'price')

            # else if the current price is below moving average, short
            elif context.monthly_price[asset][-1] < context.moving_avg[asset] and context.shares[asset] > 0:
                order(asset, -context.shares[asset])
                context.shares[asset] = 0

                # change cash amount
                context.portfolio.cash += context.shares[asset] * data.current(asset, 'price')

                # change positions value
                context.portfolio.positions_value -= context.shares[asset] * data.current(asset, 'price')

            # save/record the data for future plotting
            # record(asset = context.monthly_price[asset][-1], sma = context.moving_avg[asset])

        # calculate current portfolio_value
        context.portfolio.portfolio_value = context.portfolio.cash + context.portfolio.positions_value

        # record portfolio value
        record(portfolio = context.portfolio.portfolio_value)

        # also record the S&P 500 monthly price
        record(SPY = context.ratio * data.current(context.benchmark, 'price'))
     
def analyze(context = None, results = None):
    """
    Plots the results of the strategy against a buy-and-hold strategy.
    
    Input: n/a?
    
    Output: a plot of two superimposed curves, one being Faber's strategy and the other being a buy-and-hold strategy.
    """
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax1 = fig.add_subplot(211)

    # plot both the portfolio based on faber's strategy and a buy-and-hold strategy
    results.portfolio_value.plot(ax=ax1)
    results['SPY'].plot(ax=ax1)

    ax1.set_ylabel('Portfolio value (USD)')

    plt.show()

    tickers = []
    for symbol in context.symbol:
        symbol = str(symbol).translate(None, '0123456789[]() ')[6:]
        tickers.append(symbol)

    run('test.db', results, 'faber', tickers)
