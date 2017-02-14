#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
    Extract info from google finance stock screener.
    Author: Tan Kok Hua
    Blog: simply-python.com

    Updates:
        Jun 01 2015: Add in rename columns name functions
        May 20 2015: Update mid url as txt file

    ToDo:
        Change some of paramters names
        divdidend str: %20%26%20%28dividend_yield%20%3E%3D%200%29%20%26%20%28dividend_yield%20%3C%3D%20248%29

    Exchange str:
    SGX (default)
    HKG

"""
import os, re, sys, time, datetime, copy, calendar
import numpy as np
import pandas, pdb
from pattern.web import URL, extension, cache, plaintext
from pprint import pprint
from jsonwebretrieve import WebJsonRetrieval
import simplejson as json

class GoogleStockDataExtract(object):
    """
        Target url need to be rotate and join separately.
    """
    def __init__(self, exchange = 'SGX'):
        """ 

        """
        ## url parameters for joining
        self.target_url_start = 'https://www.google.com/finance?output=json&start=0&num=3000&noIL=1&q=[%28exchange%20%3D%3D%20%22#$%22%29%20%26%20%28'
        self.target_exchange = exchange
        self.target_url_end = ']&restype=company&ei=nX-hWOiEAY66ugS6k6PADg' # the url is changing with time, from time to time need to update
        self.temp_url_mid = ''
        self.target_full_url = ''
        current_script_folder = os.path.dirname(os.path.realpath(__file__))
        self.mid_url_list_filepath = os.path.join(current_script_folder,'bin',(self.target_exchange + '_googlescreen_url.txt'))
        
        with open(self.mid_url_list_filepath, 'r') as f:
            url_data =f.readlines()

        self.mid_url_list = [n.strip('\n') for n in url_data]

        ## parameters
        self.saved_json_file = r'./temptryyql.json'
        self.target_tag = 'searchresults' #use to identify the json data needed

        ## Result dataframe
        self.result_google_ext_df = pandas.DataFrame()

    @property
    def target_exchange(self):
        return self._target_exchange

    @target_exchange.setter
    def target_exchange(self, exchange):
        """ Will also set to the target url start string.
            Temporary set to SGX and NASDAQ

        """
        self._target_exchange = exchange
        self.target_url_start = self.target_url_start.replace('#$', self._target_exchange)


    def form_full_url(self):
        """ Form the url"""
        self.target_full_url = self.target_url_start + self.temp_url_mid + self.target_url_end
        
    def retrieve_stockdata(self):
        """ Retrieve the json file based on the self.target_full_url"""
        ds = WebJsonRetrieval()
        ds.set_url(self.target_full_url)
        ds.download_json() # default r'c:\data\temptryyql.json'

    def get_json_obj_fr_file(self):
        """ Return the json object from the .json file download.        
            Returns:
                (json obj): modified json object fr file.
        """

        with open(self.saved_json_file) as f:
            data_str = f.read() 
        # replace all the / then save back the file
        update_str = re.sub(r"\\",'',data_str)
        json_raw_data = json.loads(update_str)
        return json_raw_data

    def convert_json_to_df(self):
        """ Convert the retrieved data to dataframe
            Returns:
                (Dataframe obj): df formed from the json extact.
        """
        json_raw_data = self.get_json_obj_fr_file()
        
        new_data_list = []
        for n in json_raw_data['searchresults']:
            temp_stock_dict={'SYMBOL':n['ticker'],
                             'CompanyName':n['title'],
                            }
            for col_dict in n['columns']:
                if not col_dict['value'] == '-':
                    temp_stock_dict[col_dict['field']] = col_dict['value']
                
            new_data_list.append(temp_stock_dict)
            
        return pandas.DataFrame(new_data_list)        


    def retrieve_all_stock_data(self):
        """ Retreive all the stock data. Iterate all the target_url_mid1 """
        for temp_url_mid in self.mid_url_list:
            self.temp_url_mid = temp_url_mid
            self.form_full_url()
            self.retrieve_stockdata()
            temp_data_df = self.convert_json_to_df()
#            pdb.set_trace()
            if len(self.result_google_ext_df) == 0:
                self.result_google_ext_df = temp_data_df
            else:
                self.result_google_ext_df =  pandas.merge(self.result_google_ext_df, temp_data_df, on=['SYMBOL','CompanyName'])
        self.rename_columns() 

    def rename_columns(self):
        """ Rename some of columns to avoid confusion as from where the data is pulled.
            Some of names added the GS prefix to indicate resutls from google screener.
            Set to self.result_google_ext_df
        """
#        self.result_google_ext_df['PE'] = self.result_google_ext_df['PE'].str.replace(',','')
#        self.result_google_ext_df['PE'] = self.result_google_ext_df['PE'].astype('float')
#        self.result_google_ext_df['TotalDebtToEquityYear'] = self.result_google_ext_df['TotalDebtToEquityYear'].str.replace(',','')
#        self.result_google_ext_df['TotalDebtToEquityYear'] = self.result_google_ext_df['TotalDebtToEquityYear'].astype('float')
#        pdb.set_trace()
        self.result_google_ext_df = self.result_google_ext_df.rename(columns={
                         'DividendPerShare': 'DPS_TTM',
                         'DPSRecentYear': 'DPS_RecentYear',
                         'IAD': 'Dividend_NextYear',
                         'Dividend': 'Dividend_RecentYear',
                         'EBITDMargin': 'MarginEBITD_TTM',
                         'GrossMargin':'MarginGross_TTM',
                         'OperatingMargin': 'MarginOperating_TTM',
                         'NetProfitMarginPercent': 'MarginNetProfit_TTM',
                         'Price50DayAverage': 'PriceAverage_50Day',
                         'Price150DayAverage': 'PriceAverage_150Day',
                         'Price200DayAverage': 'PriceAverage_200Day',
                         'Price13WeekPercChange': 'PricePercChange_13Week',
                         'Price26WeekPercChange': 'PricePercChange_26Week',
                         'Price52WeekPercChange': 'PricePercChange_52Week',
                         'PE' : 'PriceToEquity',
                         'PriceSales': 'PriceToSales_TTM', 
                         'AINTCOV':'InterestCoverage_Year',
                         'ReturnOnAssets5Years': 'ROA_5years',
                         'ReturnOnAssetsTTM': 'ROA_TTM',
                         'ReturnOnAssetsYear':'ROA_year',
                         'ReturnOnEquity5Years': 'ROE_5years',
                         'ReturnOnEquityTTM': 'ROE_TTM',
                         'ReturnOnEquityYear': 'ROE_year',
                         'ReturnOnInvestment5Years': 'ROI_5years',
                         'ReturnOnInvestmentTTM': 'ROI_TTM',
                         'ReturnOnInvestmentYear': 'ROI_year',
                         'NetIncomeGrowthRate5Years': 'GrowthRateNetIncome_5years',
                         'RevenueGrowthRate5Years': 'GrowthRateRevenue_5years',
                         'RevenueGrowthRate10Years': 'GrowthRateRevenue_10years',
                         'EPSGrowthRate5Years': 'GrowthRateEPS_5years',
                         'EPSGrowthRate10Years': 'GrowthRateEPS_10years',
                         })
        firstcols = ['CompanyName', 'SYMBOL', 'MarketCap', 'Volume', 'AverageVolume', 
                  'QuoteLast', 'QuotePercChange', 'High52Week', 'Low52Week', 'Beta', 'Float'
                  ] 
                  
        t = self.result_google_ext_df.columns.tolist()
        restcols = [col for col in t if col not in firstcols]
        restcols.sort()
        finalcols = firstcols + restcols
        self.result_google_ext_df = self.result_google_ext_df[finalcols]
        
        def f(num_str):
            powers = {'T': 10 ** 12, 'B': 10 ** 9, 'M': 10 ** 6, 'K': 10 ** 3}
            match = re.search(r"([0-9\.]+)\s?(T|B|M|K)", num_str)
            if match is not None:
                quantity = match.group(1)
                magnitude = match.group(2)
                return float(quantity) * powers[magnitude]
            else:
                return float(num_str)
                
        keycols = ['CompanyName', 'SYMBOL'] # str type
        powercols = ['MarketCap', 'Volume', 'AverageVolume']
        floatcols = [col for col in finalcols if col not in (keycols + powercols)]
        for col in powercols: 
            self.result_google_ext_df[col] = self.result_google_ext_df[col].astype(str)
            self.result_google_ext_df[col] = self.result_google_ext_df[col].replace(r'^$', np.nan, regex=True) 
            self.result_google_ext_df[col] = self.result_google_ext_df[col].str.replace(',','')
            self.result_google_ext_df[col] = self.result_google_ext_df[col].apply(f)
        for col in floatcols:
            self.result_google_ext_df[col] = self.result_google_ext_df[col].astype(str)
            self.result_google_ext_df[col] = self.result_google_ext_df[col].replace(r'^$', np.nan, regex=True) 
            self.result_google_ext_df[col] = self.result_google_ext_df[col].str.replace(',','')            
            self.result_google_ext_df[col] = self.result_google_ext_df[col].astype('float')
            
#%% main()
if __name__ == '__main__':

    choice  = 2

    if choice == 2:
        hh = GoogleStockDataExtract('SGX')
        hh.retrieve_all_stock_data()

        print hh.result_google_ext_df.columns.tolist()
        hh.result_google_ext_df.to_csv(r'./temp.csv', index =False)

