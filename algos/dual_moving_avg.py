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
    context.benchmark = symbol('SPY')

    context.symbol = [symbol('XLB'),
                      symbol('XLE'),
                      symbol('XLF'), 
                      symbol('XLK'), 
                      symbol('XLP'), 
                      symbol('XLY')]

    # keep track of number of shares bought
    context.shares = defaultdict(int)
    context.long_sma = defaultdict(int)
    context.short_sma = defaultdict(int)

    # initializes certain params in handle_data that must be run only on the first event
    context.init = True

def handle_data(context, data):
    """
    Herein lies Faber's trading strategy.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing) on the last trading day of each month
    """
    money_spent = 0
    value = context.portfolio.portfolio_value

    if context.init == True:
        # to scale the S&P's value to how much our portfolio is worth
        context.ratio = context.portfolio.portfolio_value / data.current(context.benchmark, 'price')
        context.init = False

    for asset in context.symbol:
        # calculate 200-day and 20-day sma
        context.long_sma[asset] = mean(data.history(asset, 'price', 200,'1d'))
        context.short_sma[asset] = mean(data.history(asset, 'price', 20, '1d'))

    # # calculate new positions_value (since our positions should have changed value over time)
    # for asset in context.symbol:
    #     context.portfolio.positions_value += context.shares[asset] * data.current(asset, 'close')
    
    ### Trading strategy ###

    for asset in context.symbol:
        # if the short_sma > long_sma, buy
        if context.short_sma[asset] > context.long_sma[asset] and money_spent < value:
            order(asset, 500)
            context.shares[asset] += 500

            # add amount ordered to total money spent during this specific buying period
            money_spent += 500 * data.current(asset, 'price')

        # else if the current price is below moving average, short
        elif context.short_sma[asset] < context.long_sma[asset] and context.shares[asset] > 0:
            order(asset, -context.shares[asset])
            context.shares[asset] = 0

        # save/record the data for future plotting
        # record(asset = context.monthly_price[asset][-1], sma = context.moving_avg[asset])

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

    run('test.db', results, 'dual_moving_avg', tickers)

