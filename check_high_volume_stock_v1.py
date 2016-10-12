# -*- coding: utf-8 -*-
"""
Created on Sun May 29 17:19:35 2016

@author: Jennifer
"""
from __future__ import division
import sys
import os
import errno
from collections import defaultdict
from yahoo_finance import Share
from datetime import datetime
from time import time
import csv
import urllib2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.finance import candlestick_ohlc
import matplotlib
import pylab
matplotlib.rcParams.update({'font.size': 9})

if len(sys.argv) >= 2:
    writeDir = sys.argv[1]
else:
    writeDir = os.getcwd()
#    writeDir = '/Users/Jennifer/Google Drive/highVolumnStock' # for mac usage

       
def getSGX():
    '''
    read the name and symbol of SGX stock from the file SGX.txt
    '''
    stockNm = defaultdict(list)
    with open(os.getcwd() + '/SGX.txt','r') as F:
        for line in F:
            if not line.startswith('Symbol'):
                tmp = line.rstrip().split('\t')
                stockNm[tmp[0]+'.SI'].append(tmp[1])                
    print 'totally get {} SGX stock name!'.format(len(stockNm))  
    return stockNm
       
def selectStock(stocks):
    '''
    select the stock with today's trading volume at least 6 fold higher than 
    average historical trading volume
    '''
    start_time = time()
    resultStock = {}
    count = 0     
    num = 0
    for symb in stocks.keys():
        try:
            stock = Share(symb)
            vol = int(stock.get_volume())
            daily_avg_vol = int(stock.get_avg_daily_volume())
            price = float(stock.get_price())
            prevPrice = float(stock.get_prev_close())
            avg_50day = float(stock.get_50day_moving_avg())
            avg_200day = float(stock.get_200day_moving_avg())
        except (TypeError,AttributeError):
            continue
        num += 1
        volRatio = vol / daily_avg_vol
        print num,stocks[symb][0],volRatio
    
        if volRatio > 6 and price > prevPrice and price > avg_50day:
            count += 1
            stocks[symb].extend([vol, daily_avg_vol, volRatio, price, prevPrice, 
                                    avg_50day, avg_200day, 
                                    stock.get_price_earnings_ratio(),
                                    stock.get_price_book(),
                                    stock.get_short_ratio(),
                                    stock.get_dividend_yield()])
    
    resultStock = {symb:stocks[symb] for symb in stocks.keys() if len(stocks[symb]) > 1}
    print '{} stock(s) has marvelous volume'.format(count) 
    print 'total time of running: {} seconds'.format(time()-start_time)
    return resultStock
        
def writeResult(resultStock, workDir = os.getcwd()):
    '''
    generate the csv with selected stocks
    '''
    result2Write = []
    for symb in resultStock.keys():
        tmp = [symb]
        for i in range(len(resultStock[symb])):        
            tmp.append(resultStock[symb][i])
        result2Write.append(['NA' if v is None else v for v in tmp])          
    resultFile = workDir + '/checkHighVolume_'+datetime.now().strftime('%Y-%m-%d-%H-%M')+'.csv'
    with open(resultFile, 'wb') as outF:
        a = csv.writer(outF,delimiter = ',')
        a.writerows([['symbol', 'stockName', 'volume', 'avg_volume', 'volume_ratio',
                    'price', 'pre_price', 'avg_50_day', 'avg_200_day', 'PEratio',
                    'priceBook', 'short_ratio', 'dividend_yield']])                
        a.writerows(result2Write)    
    return
 
#%% for ploting       
def rsiFunc(prices, n=14):
    deltas = np.diff(prices)
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100./(1.+rs)

    for i in range(n, len(prices)):
        delta = deltas[i-1] # cause the diff is 1 shorter

        if delta>0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(n-1) + upval)/n
        down = (down*(n-1) + downval)/n

        rs = up/down
        rsi[i] = 100. - 100./(1.+rs)

    return rsi

def movingaverage(values,window):
    weigths = np.repeat(1.0, window)/window
    smas = np.convolve(values, weigths, 'valid')
    return smas # as a numpy array

def ExpMovingAverage(values, window):
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    a =  np.convolve(values, weights, mode='full')[:len(values)]
    a[:window] = a[window]
    return a
    
def computeMACD(x, slow=26, fast=12):
    """
    compute the MACD (Moving Average Convergence/Divergence) using a fast and slow exponential moving avg'
    return value is emaslow, emafast, macd which are len(x) arrays
    """
    emaslow = ExpMovingAverage(x, slow)
    emafast = ExpMovingAverage(x, fast)
    return emaslow, emafast, emafast - emaslow
          
def graphStock(stock, MA1, MA2, writeDir = os.getcwd()):
    '''
        Use this to dynamically pull a stock:
    '''
    # pulling data
    try:
        print 'Currently Pulling',stock
        print str(datetime.fromtimestamp(int(time())).strftime('%Y-%m-%d %H:%M:%S'))
        urlToVisit = 'http://chartapi.finance.yahoo.com/instrument/1.0/'+stock+'/chartdata;type=quote;range=1y/csv'
        stockFile =[]
        try:
            sourceCode = urllib2.urlopen(urlToVisit).read()
            splitSource = sourceCode.split('\n')
            for eachLine in splitSource:
                splitLine = eachLine.split(',')
                if len(splitLine)==6:
                    if 'values' not in eachLine:
                        stockFile.append(eachLine)
        except Exception, e:
            print str(e), 'failed to organize pulled data.'
    except Exception,e:
        print str(e), 'failed to pull pricing data'
    # plot
    try:   
        date, closep, highp, lowp, openp, volume = np.loadtxt(stockFile,delimiter=',', unpack=True,
                                                              converters={ 0: mdates.strpdate2num('%Y%m%d')})
        x = 0
        y = len(date)
        newAr = []
        while x < y:
            appendLine = date[x],openp[x],highp[x],lowp[x],closep[x],volume[x]
            newAr.append(appendLine)
            x+=1
            
        Av1 = movingaverage(closep, MA1)
        Av2 = movingaverage(closep, MA2)

        SP = len(date[MA2-1:])
            
        fig = plt.figure(facecolor='#07000d')

        ax1 = plt.subplot2grid((6,4), (1,0), rowspan=4, colspan=4, axisbg='#07000d')
        candlestick_ohlc(ax1, newAr[-SP:], width=.6, colorup='#53c156', colordown='#ff1717')

        Label1 = str(MA1)+' SMA'
        Label2 = str(MA2)+' SMA'

        ax1.plot(date[-SP:],Av1[-SP:],'#e1edf9',label=Label1, linewidth=1.5)
        ax1.plot(date[-SP:],Av2[-SP:],'#4ee6fd',label=Label2, linewidth=1.5)
        
        ax1.grid(True, color='w')
        ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.yaxis.label.set_color("w")
        ax1.spines['bottom'].set_color("#5998ff")
        ax1.spines['top'].set_color("#5998ff")
        ax1.spines['left'].set_color("#5998ff")
        ax1.spines['right'].set_color("#5998ff")
        ax1.tick_params(axis='y', colors='w')
        plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='upper'))
        ax1.tick_params(axis='x', colors='w')
        plt.ylabel('Stock price and Volume')

        maLeg = plt.legend(loc=9, ncol=2, prop={'size':7},
                   fancybox=True, borderaxespad=0.)
        maLeg.get_frame().set_alpha(0.4)
        textEd = pylab.gca().get_legend().get_texts()
        pylab.setp(textEd[0:5], color = 'w')

        volumeMin = 0
        
        ax0 = plt.subplot2grid((6,4), (0,0), sharex=ax1, rowspan=1, colspan=4, axisbg='#07000d')
        rsi = rsiFunc(closep)
        rsiCol = '#c1f9f7'
        posCol = '#386d13'
        negCol = '#8f2020'
        
        ax0.plot(date[-SP:], rsi[-SP:], rsiCol, linewidth=1.5)
        ax0.axhline(70, color=negCol)
        ax0.axhline(30, color=posCol)
        ax0.fill_between(date[-SP:], rsi[-SP:], 70, where=(rsi[-SP:]>=70), facecolor=negCol, edgecolor=negCol, alpha=0.5)
        ax0.fill_between(date[-SP:], rsi[-SP:], 30, where=(rsi[-SP:]<=30), facecolor=posCol, edgecolor=posCol, alpha=0.5)
        ax0.set_yticks([30,70])
        ax0.yaxis.label.set_color("w")
        ax0.spines['bottom'].set_color("#5998ff")
        ax0.spines['top'].set_color("#5998ff")
        ax0.spines['left'].set_color("#5998ff")
        ax0.spines['right'].set_color("#5998ff")
        ax0.tick_params(axis='y', colors='w')
        ax0.tick_params(axis='x', colors='w')
        plt.ylabel('RSI')

        ax1v = ax1.twinx()
        ax1v.fill_between(date[-SP:],volumeMin, volume[-SP:], facecolor='#00ffe8', alpha=.4)
        ax1v.axes.yaxis.set_ticklabels([])
        ax1v.grid(False)
        ###Edit this to 3, so it's a bit larger
        ax1v.set_ylim(0, 3*volume.max())
        ax1v.spines['bottom'].set_color("#5998ff")
        ax1v.spines['top'].set_color("#5998ff")
        ax1v.spines['left'].set_color("#5998ff")
        ax1v.spines['right'].set_color("#5998ff")
        ax1v.tick_params(axis='x', colors='w')
        ax1v.tick_params(axis='y', colors='w')
        ax2 = plt.subplot2grid((6,4), (5,0), sharex=ax1, rowspan=1, colspan=4, axisbg='#07000d')
        fillcolor = '#00ffe8'
        nslow = 26
        nfast = 12
        nema = 9
        emaslow, emafast, macd = computeMACD(closep)
        ema9 = ExpMovingAverage(macd, nema)
        ax2.plot(date[-SP:], macd[-SP:], color='#4ee6fd', lw=2)
        ax2.plot(date[-SP:], ema9[-SP:], color='#e1edf9', lw=1)
        ax2.fill_between(date[-SP:], macd[-SP:]-ema9[-SP:], 0, alpha=0.5, facecolor=fillcolor, edgecolor=fillcolor)

        plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='upper'))
        ax2.spines['bottom'].set_color("#5998ff")
        ax2.spines['top'].set_color("#5998ff")
        ax2.spines['left'].set_color("#5998ff")
        ax2.spines['right'].set_color("#5998ff")
        ax2.tick_params(axis='x', colors='w')
        ax2.tick_params(axis='y', colors='w')
        plt.ylabel('MACD', color='w')
        ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='upper'))
        for label in ax2.xaxis.get_ticklabels():
            label.set_rotation(45)

        plt.suptitle(stock.upper(),color='w')

        plt.setp(ax0.get_xticklabels(), visible=False)
        plt.setp(ax1.get_xticklabels(), visible=False)

        plt.subplots_adjust(left=.09, bottom=.14, right=.94, top=.95, wspace=.20, hspace=0)
        plt.show()
        # save the figure
        figNm = writeDir + '/' + datetime.now().strftime('%Y-%m-%d') + '/' + stock +'.jpg'
        if not os.path.exists(os.path.dirname(figNm)):
            try:
                os.makedirs(os.path.dirname(figNm))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise     
        fig.savefig(figNm, dpi = 900, facecolor=fig.get_facecolor())
           
    except Exception,e:
        print 'main loop',str(e)
       
    return

#%% main
if __name__ == "__main__":
#    writeDir = '/Users/Jennifer/Google Drive/highVolumnStock' # for Jennifer's mac usage
    writeDir = os.getcwd()
    SGX_stocks = getSGX()
    high_volume_stock = selectStock(SGX_stocks)
    writeResult(high_volume_stock, writeDir)
    # plot the result
    for symb in high_volume_stock.keys():
        graphStock(symb, 50, 100, writeDir)
