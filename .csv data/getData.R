# prompt for relevant packages
# I require quantstrat (although it may not be necessary) because quantmod is also intrinsically required
require(quantstrat)

# set initial date we want to gather data from
initDate='2009-09-01'

# declare tickers of interest
currency("USD")
symbols = c("XLF", "XLE", "XLY", "XLB", "XLK", "XLP")
for(symbol in symbols){ # establish tradable instruments
  stock(symbol, currency="USD",multiplier=1)
}

# load data with quantmod
getSymbols(symbols, src='yahoo', index.class=c("POSIXt","POSIXct"), from=initDate)
for(symbol in symbols) {
  x<-get(symbol)
  x<-to.monthly(x,indexAt='lastof',drop.time=TRUE)
  indexFormat(x)<-'%Y-%m-%d'
  colnames(x)<-gsub("x",symbol,colnames(x))
  assign(symbol,x)
}

# export data to .csv
for(symbol in symbols) {
  filename = paste(symbol, '.csv', sep="")
  write.csv(symbol, file=filename)
}




