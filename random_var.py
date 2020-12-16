import yfinance
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import statistics
import math
import time

def get_stock_data(stock):
    data = yfinance.Ticker(stock)
    df = pd.DataFrame(data.history(period="2y"))
    adjusted_close = df['Close']
    df['daily_pct_change'] = df['Close'].pct_change()
    mean_return = df["daily_pct_change"].mean()
    std_return = df["daily_pct_change"].std()
    return monte_carlo_sim(mean_return, std_return, float(df['Close'][-1]))



def monte_carlo_sim(mean_return, std_return, initial_price):
    simulation = {}
    final_price = []
    for sim in range(1, 1000):
        simulation["sim_" + str(sim)] = []
        price = initial_price # set the initial price
        for i in range(14):
            new_price = price*(mean_return + std_return*np.random.normal())
            price = price + new_price
            simulation["sim_" + str(sim)] += [price]
        final_price += [price]
    return  statistics.stdev(final_price) / statistics.mean(final_price)
