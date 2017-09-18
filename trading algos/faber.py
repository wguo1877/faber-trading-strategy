import sys
sys.path.append('C:/Users/William/Documents/GitHub/faber-trading-strategy/algos')
from numpy import mean
from collections import defaultdict
from zipline.api import order, order_target, record, symbol, date_rules, time_rules, schedule_function, set_slippage, slippage
from write_to_sql import run
import pandas as pd

from zipline import TradingAlgorithm
from zipline.finance import commission

priorOpen = None
priorClose = None

def initialize(context):
    """
    Stores the names of the stocks we'll be looking at.
    
    Input: a persistent namespace where we store an SID/list of SIDs
    
    Output: n/a
    """
    # set_slippage(TradeAtTheCloseSlippageModel(priorOpen,priorClose,0.0))
    context.set_commission(commission.PerShare(cost=0))

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

    context.moving_avg = defaultdict(int)
    context.monthly_price = defaultdict(list) 

    # keeps track of which assets to trade 
    context.buy = []
    context.sell = []

    # skip the first 10 months so that we have enough data to establish our moving average    
    schedule_function(get_assets, date_rules.month_end(), time_rules.market_open(minutes=1))

def handle_data(context, data):
    """
    Calls the trading strategy function at the end of every month.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing)
    """
    pass

def get_assets(context, data):
    """
    Although we actually trade at the beginning of the trading month, the way Zipline handles orders is that the fill prices of orders
    are the next bar's closing price. We have a list of assets we want to trade and we order_target() them, allowing us to purchase
    using the end of the previous month's closing price.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: a list of assets to trade
    """    
    context.skip += 1

    context.buy = []
    context.sell = []

    if context.skip < 10:
        for asset in context.symbol:
            price = data.current(asset, 'close')
            context.monthly_price[asset].append(price)

    else:
        if context.skip == 10:
            context.ratio = context.portfolio.portfolio_value / data.current(context.benchmark, 'close')

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
                # context.buy.append(asset)
                order_target(asset,50)

            # else if the current price is below moving average and we have 500 shares of the asset, sell
            elif context.monthly_price[asset][-1] < context.moving_avg[asset]:
                # context.sell.append(asset)
                order_target(asset, 0)

        record(poop = context.portfolio.portfolio_value)
        record(SPY = context.ratio * data.current(context.benchmark, 'close'))

    global priorOpen
    global priorClose
    
    priorOpen = {}
    priorClose = {}
    
    for sid in data:
        priorOpen[sid] = data[sid].open_price
        priorClose[sid] = data[sid].close_price
        # print sid.symbol+' prior open/close: '+str(priorOpen[sid])+'/'+str(priorClose[sid])

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
    results['poop'].plot(ax=ax1)
    results['SPY'].plot(ax=ax1)
    ax1.set_ylabel('Portfolio value (USD)')

    ax2 = fig.add_subplot(212)
    results['returns'].plot(ax=ax2)
    ax2.set_ylabel('Cumulative Returns')

    plt.show()

    # import pyfolio as pf

    # returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(results)
    # returns.to_csv("returns.csv")
    # pf.create_simple_tear_sheet(returns, positions=positions, transactions=transactions)

    # tickers = []
    # for symbol in context.symbol:
    #     symbol = str(symbol).translate(None, '0123456789[]() ')[6:]
    #     tickers.append(symbol)

    # run('test.db', results, 'faber', tickers)

########################################################  
# Slippage model to trade at the prior close or at a fraction of the prior open - close range.  
class TradeAtTheCloseSlippageModel(slippage.SlippageModel):  
    '''Class for slippage model to allow trading at the prior close  
       or at a fraction of the prior open to close range.  
    '''  
    # Constructor, self and fraction of the prior open to close range to add (subtract)  
    # from the prior open to model executions more optimistically  
    def __init__(self, priorOpen,priorClose,fractionOfOpenCloseRange):

        # Store the percent of prior open - close range to take as the execution price  
        self.priorOpen = priorOpen
        self.priorClose = priorClose
        self.fractionOfOpenCloseRange = fractionOfOpenCloseRange

    def process_order(self, trade_bar, order):

        openPrice = priorOpen[order.sid]  
        closePrice = priorClose[order.sid]  
        ocRange = closePrice - openPrice  
        ocRange = ocRange * self.fractionOfOpenCloseRange  
        if (ocRange != 0.0):  
            targetExecutionPrice = closePrice - ocRange  
        else:  
            targetExecutionPrice = closePrice  

        return (targetExecutionPrice, order.amount)