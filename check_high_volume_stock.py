# -*- coding: utf-8 -*-
"""
Created on Sun May 29 17:19:35 2016

@author: Jennifer
"""
from __future__ import division
import sys
import os
from collections import defaultdict
from yahoo_finance import Share
from datetime import datetime
from time import time
import csv

if len(sys.argv) >= 2:
    writeDir = sys.argv[1]
else:
    writeDir = os.getcwd()
    writeDir = '/Users/Jennifer/Google Drive/highVolumnStock'

class checkHighVolume:   
    def __init__(self, workDir = os.getcwd()):
        self.stockNm = defaultdict(list)
        self.resultStock = {}
        SGX_name_list = workDir + '/SGX.txt'
        with open(SGX_name_list,'r') as F:
            for line in F:
                if not line.startswith('Symbol'):
                    tmp = line.rstrip().split('\t')
                    self.stockNm[tmp[0]+'.SI'].append(tmp[1])                
        print 'totally get {} SGX stock name!'.format(len(self.stockNm))
        self.select_stock()
        self.write_result(writeDir)
        
    def select_stock(self):
        start_time = time()
        count = 0     
        num = 0
        for symb in self.stockNm.keys():
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
            print num,self.stockNm[symb][0],volRatio
        
            if volRatio > 6 and price > prevPrice and price > avg_50day:
                count += 1
                self.stockNm[symb].extend([vol, daily_avg_vol, volRatio, price, prevPrice, 
                                        avg_50day, avg_200day, 
                                        stock.get_price_earnings_ratio(),
                                        stock.get_price_book(),
                                        stock.get_short_ratio(),
                                        stock.get_dividend_yield()])
        
        self.resultStock = {symb:self.stockNm[symb] for symb in self.stockNm.keys() if len(self.stockNm[symb]) > 1}
        print '{} stock(s) has marvelous volume'.format(count) 
        print 'total time of running: {} seconds'.format(time()-start_time)
        return
        
    def write_result(self,workDir = os.getcwd()):
        result2Write = []
        for symb in self.resultStock.keys():
            tmp = [symb]
            for i in range(len(self.resultStock[symb])):        
                tmp.append(self.resultStock[symb][i])
            result2Write.append(['NA' if v is None else v for v in tmp])          
        resultFile = workDir + '/checkHighVolume_'+datetime.now().strftime('%Y-%m-%d-%H-%M')+'.csv'
        with open(resultFile, 'wb') as outF:
            a = csv.writer(outF,delimiter = ',')
            a.writerows([['symbol', 'stockName', 'volume', 'avg_volume', 'volume_ratio',
                        'price', 'pre_price', 'avg_50_day', 'avg_200_day', 'PEratio',
                        'priceBook', 'short_ratio', 'dividend_yield']])                
            a.writerows(result2Write)    
        return
        
    def plot(self):
        '''
        Use this to dynamically pull a stock:
        '''
        try:
            print 'Currently Pulling',stock
            print str(datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'))
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
        try:   
            date, closep, highp, lowp, openp, volume = np.loadtxt(stockFile,delimiter=',', unpack=True,
                                                                  converters={ 0: mdates.strpdate2num('%Y%m%d')})
            x = 0
            y = len(date)
            newAr = []
            while x < y:
                appendLine = date[x],openp[x],closep[x],highp[x],lowp[x],volume[x]
                newAr.append(appendLine)
                x+=1

            Av1 = movingaverage(closep, MA1)
            Av2 = movingaverage(closep, MA2)
                
runable = checkHighVolume()                
   
