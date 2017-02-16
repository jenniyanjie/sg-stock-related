#!/usr/local/bin/python2.7
from __future__ import division
import string, re, os, time, smtplib, sys, urllib2, pandas
from urllib import urlopen
from datetime import datetime
import httplib, urllib #used in the Pushover code
#import numpy as np
import requests
import json

def quote_grab(symbol):
   
    baseurl = 'http://google.com/finance?q='
    urlData = urlopen(baseurl + symbol)
   
    print 'Opening Google Finance URL...'

    # Another option: namestr = re.compile('.*name:\"' + symbol + '\",cp:(.*),p:(.*?),cid(.*)}.*')
    namestr = re.compile('.*name:\"' + symbol + '\",cp:(.*),p:(.*?),cid(.*)') 
    # "?" used as there is a second string "cid" in the page and the Match was being done up to that one. The "?" keeps it to the 1st occurrence.
   
    print 'Checking quotes for ' + symbol
   
    for line in urlData:
       
        m = re.match(namestr, line)
       
        if m:
            #Since the method m.group(2) returns a string in the form "xxxx", it cannot be converted to float,
            #therefore I strip the "" from that string and pass it to the float function.
            priceStr = m.group(2).strip('"')
            price = float(priceStr)
  
    urlData.close()
    return price #returns price as a float

def quoteGrab(symbols):
    '''
    grab the last price and previous close price for the symb in symbols
    symbols: a list of symbols
    
    '''
    baseurl = 'http://finance.yahoo.com/d/quotes.csv?s='
    midurl = ('+').join(symbols)
    endurl = '&f=sva2l1pm3' #TODO: edit the field
    pricecsv = urllib2.urlopen(baseurl + midurl + endurl).read()
    df = pandas.DataFrame([line.split(',') for line in pricecsv.strip('\n').split('\n')], 
                       columns = ["SYMBOL", "Volume", "AverageVolume", "LastQuote", "PreviousClose","AvgPrice_50day"])
    for col in df.columns.tolist():
        if col == "SYMBOL":
            continue
        df[col] = df[col].astype('float')
    
    df['hpr'] = df['LastQuote']/df['PreviousClose'] - 1 
    df['chg'] = ['up' if x >= 0 else 'down' for x in df['hpr']]
    df['chgV'] = abs(df['hpr'])
    df_sele = df.loc[(df['pChg'] > 0.2) | (df['pChg'] < -0.15), ]
    return df_sele

def pushover(token, user, msg):

    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.urlencode({
            "token": token, #"INSERT YOUR TOKEN HERE"
            "user": user, #"INSERT YOUR API USER KEY HERE"
            "message": msg,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()


 
def pushbullet(title, body):
    """ Sending notification via pushbullet.
        Args:
            title (str) : title of text.
            body (str) : Body of text.
    """
    data_send = {"type": "note", "title": title, "body": body}
 
    ACCESS_TOKEN = 'your_access_token'
    resp = requests.post('https://api.pushbullet.com/v2/pushes', data=json.dumps(data_send),
                         headers={'Authorization': 'Bearer ' + ACCESS_TOKEN, 'Content-Type': 'application/json'})
    if resp.status_code != 200:
        raise Exception('Something wrong')
    else:
        print 'complete sending'
        
def send_email(sbjt, msg):
    fromaddr = 'jenniyanjie@gmail.com'
    toaddrs = 'jennyyanjennyyan@gmail.com'
    bodytext = 'From: %s\nTo: %s\nSubject: %s\n\n%s' %(fromaddr, toaddrs, sbjt, msg)
   
    # Credentials (if needed)
    username = 'jenniyanjie@gmail.com' #'USERNAME@gmail.com'
    password = 'Sdfz880201' 
  
    # The actual mail sent
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, bodytext)
    server.quit()

#------------------------
# Constants
file = sys.argv[1]
'''
name, token, user, emailaddress, stocklist\n
'''
#------------------------

# Opens .cvs file, gets string at last line, converts it to list so that the comparison in the
# IF statement below can be done
#csvFile = open(file, 'r')
#body = 'Changes:\n'
#chg = False
#
#for line in csvFile:
#    linelst = line.split(',')
#    quote = quote_grab(linelst[0])
#   
#    if quote>float(linelst[1]) and linelst[2]==('a\n' or 'a'):
#        body = body + 'Price for %s went up to %s (threshold = %s)\n' % (linelst[0], quote, linelst[1])
#        chg = True
#    if quote<float(linelst[1]) and linelst[2]==('b\n' or 'b'):
#        body = body + 'Price for %s went down to %s (threshold = %s)\n' % (linelst[0], quote, linelst[1])
#        chg = True
#   
#if chg:
#    print 'sending email...'
#    send_email('Stock Price Changes',body)
#    print 'sending message to pushover...'
#    pushover(body)
#   
#csvFile.close()
#%% main()

if __name__ == '__main__':
    body = 'Major Price Changes:\n'
    
    symbols = ['AAPL', 'AWX.SI', 'BN2.SI'] # TODO: where to get the symbols
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M')
    price_df = quoteGrab(symbols)
    if not price_df.size == 0:
        for row in price_df.itertuples(index=True, name='Pandas'):
            body = body + 'Price for {0} went {1} to {2:.2f}% with last quote {3}'.format(getattr(row, "SYMBOL").strip('"'), getattr(row, "chg"), getattr(row, "chgV"), getattr(row, "LastQuote"))
        
        print 'sending email...' # apply a gmail accont
        send_email('Stock Price Changes' + timestamp, body)
        print 'sending message to pushover...'
        pushbullet('Stock Price Changes' + timestamp, body)
    
