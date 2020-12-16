import yfinance
import pandas as pd
import numpy as np
import datetime
import math
import statistics
import time


def find_mean(fund):
    if len(fund) == 0:
        return 0
    return np.nanmean(fund)

def find_sd(fund):
    if len(fund) == 0:
        return 0
    return np.nanstd(fund)

def options_analysis(stock, current_price):
    stock = yfinance.Ticker(stock)
    expirations = stock.options[0] # closest expiration date
    options = stock.option_chain(expirations)
    calls = options.calls
    puts = options.puts
    call_chain = call_chain_analysis(calls)
    put_chain = put_chain_analysis(puts)
    return call_put_split(float(current_price), call_chain, put_chain)




def call_put_split(current_price, call_chain, put_chain):
    """ Returns true if the call volume and impliedint point to rise """
    if len(call_chain) > len(put_chain):
        if abs(float(call_chain[0][0]) - current_price) > abs(float(put_chain[0][0]) - current_price):
             # if spread is greater for call -> watch for covered calls
             return 0
        else:
            return 1
    else:
        return 0



def call_chain_analysis(calls):
    # use open interest and volume
    inTheMoney = np.array(calls['inTheMoney'])
    strike = np.array(calls['strike'])
    lastPrice = np.array(calls['lastPrice'])

    call_volume = np.array(calls['volume'])
    mean_vol = find_mean(call_volume)
    sd_vol = find_sd(call_volume)

    openInterest = np.array(calls['openInterest'])
    mean_interest = find_mean(openInterest)
    sd_interest = find_sd(openInterest)

    move = np.array(calls['impliedVolatility'])
    call_list = []

    for i in range(len(call_volume)):
        if inTheMoney[i] == False:
            if call_volume[i] >= mean_vol + sd_vol and openInterest[i] >= mean_interest + sd_interest:
                call_list += [[strike[i], move[i], call_volume[i], openInterest[i]]] # strike, impliedVol, volume, openInterest
    return call_list

def put_chain_analysis(puts):
    # user open interest and volume
    inTheMoney = np.array(puts['inTheMoney'])
    strike = np.array(puts['strike'])
    lastPrice = np.array(puts['lastPrice'])

    put_volume = np.array(puts['volume'])
    mean_vol = find_mean(put_volume)
    sd_vol = find_sd(put_volume)

    openInterest = np.array(puts['openInterest'])
    mean_interest = find_mean(openInterest)
    sd_interest = find_sd(openInterest)

    move = np.array(puts['impliedVolatility'])
    put_list = []

    for i in range(len(put_volume)):
        if inTheMoney[i] == False:
            if put_volume[i] >= mean_vol + sd_vol and openInterest[i] >= mean_interest + sd_interest:
                put_list += [[strike[i], move[i], put_volume[i], openInterest[i]]] # strike, impliedVol, volume, openInterest

    return put_list
