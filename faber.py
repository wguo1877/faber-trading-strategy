from zipline.api import order, record, symbol, date_rules, time_rules, schedule_function

def initialize(context):
    """
    Stores the names of the stocks we'll be looking at.
    
    Input: a persistent namespace where we store an SID/list of SIDs
    
    Output: n/a
    """
    context.symbol = [symbol('AAPL'),
                      symbol('MSFT'),
                      symbol('AMZN'),
                      symbol('JPM')]

    # keep track of number of shares bought
    context.shares = {}
    for asset in context.symbol:
        context.shares[asset] = 0

    # skip the first 300 days of the timeframe so that we have enough data to calculate our 10 month SMA
    context.skip = 0

def handle_data(context, data):
    """
    Calls the trading strategy function at the end of every month.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing)
    """
    # skip the first 100 days so that we have enough data to establish our moving average
    context.skip += 1
    if context.skip < 300:
        pass
    else:
        # we only trade on the last trading day of each month; check here if it's the last day
        schedule_function(trade, date_rules.month_end(), time_rules.market_close())
    
def trade(context, data):
    """
    Herein lies Faber's trading strategy.
    
    Input: persistent namespace with SID(s) 'context', event-frame that handles look-ups of historical/current pricing data
    
    Output: some kind of action (buy/sell/nothing) on the last trading day of each month
    """
    # Compute SMA
    moving_avg = {}
    monthly_price = {}

    for asset in context.symbol:
        # calculate the 10-month (300 day) moving average of each asset
        moving_avg[asset] = data.history(asset, 'close', 300, '1d').mean()

        # Get closing price on last trading day of month
        monthly_price[asset] = data.current(asset, 'close')
    
    ### Faber's trading strategy ###
    
    # if the current price exceeds moving average, long
    for asset in context.symbol:
        if monthly_price[asset] > moving_avg[asset]:
            order(asset, 10)
            context.shares[asset] += 10

        # else if the current price is below moving average, short
        elif monthly_price[asset] < moving_avg[asset]:
            order(asset, context.shares[asset])
            context.shares[asset] = 0

        # save/record the data for future plotting
        record(asset = monthly_price[asset], sma = moving_avg[asset])
    
def analyze(context = None, results = None):
    """
    Plots the results of the strategy against a buy-and-hold strategy.
    
    Input: n/a?
    
    Output: a plot of two superimposed curves, one being Faber's strategy and the other being a buy-and-hold strategy.
    """
    import matplotlib.pyplot as plt
    import logbook
    logbook.StderrHandler().push_application()
    log = logbook.Logger('Algorithm')

    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    results.portfolio_value.plot(ax=ax1)
    ax1.set_ylabel('Portfolio value (USD)')

    ax2 = fig.add_subplot(212)
    ax2.set_ylabel('Price (USD)')

    # If data has been record()ed, then plot it.
    # Otherwise, log the fact that no data has been recorded.
    # if ('AAPL' in results and 'sma' in results):
        # results['AAPL'].plot(ax=ax2)
        # results['sma'].plot(ax=ax2)

        # trans = results.ix[[t != [] for t in results.transactions]]
        # buys = trans.ix[[t[0]['amount'] > 0 for t in
        #                  trans.transactions]]
        # sells = trans.ix[
        #     [t[0]['amount'] < 0 for t in trans.transactions]]
        # ax2.plot(buys.index, results.sma.ix[buys.index],
        #          '^', markersize=10, color='m')
        # ax2.plot(sells.index, results.sma.ix[sells.index],
        #          'v', markersize=10, color='k')
        # plt.legend(loc=0)
    # else:
    #     msg = 'Data not captured using record().'
    #     ax2.annotate(msg, xy=(0.1, 0.5))
    #     log.info(msg)

    plt.show()     