import yfinance
import pandas as pd
import statistics

def get_historical_data(stock):
    """ gets historical stock data for a given symbol """
    data = yfinance.Ticker(stock)
    return pd.DataFrame(data.history(period="2y"))

def get_volume_only(df):
    return list(df['Volume'])

def get_volume_data(df):
    """
        Calculates needed volume data from a given dataframe
        returns (average_volume_ratio, two_week_average_ratio) ratios list
    """
    volume = list(df['Volume'])
    volume_to_average_volume_ratio = []
    volume_to_two_week_volume_ratio = [0]*9
    for i in range(len(volume)):
        volume_to_average_volume_ratio += [volume[i]/sum(volume[0:i+1]) / (i+1)]
        if i >= 9:
            volume_to_two_week_volume_ratio += [volume[i]/(sum(volume[i-9:i+1])/10)]
    return (volume_to_average_volume_ratio, volume_to_two_week_volume_ratio)

def get_sd(stock_list):
    return statistics.stdev(stock_list)

def get_returns(df):
    """
        returns a list of returns for a given dataframe
    """
    open = list(df['Open'])
    close = list(df['Close'])
    returns = []
    for i in range(len(open)):
        returns += [((open[i]-close[i])/open[i])*100]
    return returns

def get_ratio_and_volume_list(volume_to_average_volume_ratio, volume_to_two_week_volume_ratio, returns):
    """
        returns tupled list of (return, volume_to_average_volume_ratio, volume_to_two_week_volume_ratio)
        for given stock. Inputs can be calculated using functions above.
    """
    tupled_ratio_and_return = []
    for i in range(len(returns)):
        tupled_ratio_and_return += [(returns[i], volume_to_average_volume_ratio[i], volume_to_two_week_volume_ratio[i])]
    return tupled_ratio_and_return

def get_mean(stock_list):
    """ returns tuple of stdev and mean for a given list """
    return statistics.mean(stock_list)

def find_return_probabilities(returns_list, return_mean):
    """
        finds probabilitiy of each outcome given a list of recent
        returns. returns (pr(high_return), pr(low_return))
    """
    high_return = 0
    low_return = 0

    high_prev_and_high_day = 0
    high_prev_and_low_day = 0
    low_prev_and_high_day = 0
    low_prev_and_low_day = 0

    count = 0
    for i in range(1, len(returns_list)):
        count += 1
        if returns_list[i-1] > return_mean:
            if returns_list[i] > return_mean:
                high_return += 1
                high_prev_and_high_day += 1
            else:
                low_return += 1
                high_prev_and_low_day += 1
        else:
            if returns_list[i] > return_mean:
                high_return += 1
                low_prev_and_high_day += 1
            else:
                low_return += 1
                low_prev_and_low_day += 1
    if returns_list[len(returns_list)-1] > return_mean:
        # (high high, high low)
        return ((high_prev_and_high_day/count)/(high_return/count), (high_prev_and_low_day/count)/(low_return/count))
    else:
        # (low high, low low)
        return ((low_prev_and_high_day/count)/(high_return/count), (low_prev_and_low_day/count)/(low_return/count))


def find_volume_probabilities(day_volume_ratio, day_two_week_volume_ratio, tupled_ratio_and_return, mean_return, mean_two_week_volume_ratio, mean_volume_ratio):
    """
        finds probability of each outcome given the tupled_ratio_and_return list.
        outcomes are as follows:
            3 standard deviations from mean, both above and below
    """

    v_avg_high_and_v_2w_high_and_return_high = 0
    v_avg_high_and_v_2w_high_and_return_low = 0

    v_avg_high_and_v_2w_low_and_return_high = 0
    v_avg_high_and_v_2w_low_and_return_low = 0

    v_avg_low_and_v_2w_high_and_return_high = 0
    v_avg_low_and_v_2w_high_and_return_low = 0

    v_avg_low_and_v_2w_low_and_return_high = 0
    v_avg_low_and_v_2w_low_and_return_low = 0

    v_avg_high_and_v_2w_high = 0
    v_avg_high_and_v_2w_low = 0
    v_avg_low_and_v_2w_high = 0
    v_avg_low_and_v_2w_low = 0

    count = 0

    for tuple in tupled_ratio_and_return:
        count += 1
        day_return = tuple[0]
        v_avg = tuple[1]
        v_2w = tuple[2]

        v_avg_high = False
        v_avg_low = False

        if (v_avg >= mean_volume_ratio):
            v_avg_high = True
        else:
            v_avg_low = True

        v_2w_high = False
        v_2w_low = False

        if (v_2w >= mean_two_week_volume_ratio):
            v_2w_high = True
        else:
            v_2w_low = True

        return_high = False
        return_low = False

        if (day_return >= mean_return):
            return_high = True
        else:
            return_low = True

        if v_avg_high and v_2w_high:
            v_avg_high_and_v_2w_high += 1
        if v_avg_high and v_2w_low:
            v_avg_high_and_v_2w_low += 1
        if v_avg_low and v_2w_high:
            v_avg_low_and_v_2w_high += 1
        if v_avg_low and v_2w_low:
            v_avg_low_and_v_2w_low += 1


        if v_avg_high and v_2w_high and return_high:
            v_avg_high_and_v_2w_high_and_return_high += 1
        if v_avg_high and v_2w_high and return_low:
            v_avg_high_and_v_2w_high_and_return_low += 1
        if v_avg_high and v_2w_low and return_high:
            v_avg_high_and_v_2w_low_and_return_high += 1
        if v_avg_high and v_2w_low and return_low:
            v_avg_high_and_v_2w_low_and_return_low += 1
        if v_avg_low and v_2w_high and return_high:
            v_avg_low_and_v_2w_high_and_return_high += 1
        if v_avg_low and v_2w_high and return_low:
            v_avg_low_and_v_2w_high_and_return_low += 1
        if v_avg_low and v_2w_low and return_high:
            v_avg_low_and_v_2w_low_and_return_high += 1
        if v_avg_low and v_2w_low and return_low:
            v_avg_low_and_v_2w_low_and_return_low += 1

    if day_volume_ratio > mean_volume_ratio:
        if day_two_week_volume_ratio > mean_two_week_volume_ratio:
            # (high high high, high high low)
            return ((v_avg_high_and_v_2w_high_and_return_high/count)/(v_avg_high_and_v_2w_high/count), (v_avg_high_and_v_2w_high_and_return_low/count)/(v_avg_high_and_v_2w_high/count))
        else:
            # (high low high, high low low)
            return ((v_avg_high_and_v_2w_low_and_return_high/count)/(v_avg_high_and_v_2w_low/count), (v_avg_high_and_v_2w_low_and_return_low/count)/(v_avg_high_and_v_2w_low/count))
    else:
        if day_two_week_volume_ratio > mean_two_week_volume_ratio:
            # (low high high, low high low)
            return ((v_avg_low_and_v_2w_high_and_return_high/count)/(v_avg_low_and_v_2w_high/count), (v_avg_low_and_v_2w_high_and_return_low/count)/(v_avg_low_and_v_2w_high/count))
        else:
            # (low low high, low low low)
            return ((v_avg_low_and_v_2w_low_and_return_high/count)/(v_avg_low_and_v_2w_low/count), (v_avg_low_and_v_2w_low_and_return_low/count)/(v_avg_low_and_v_2w_low/count))
