import robin_stocks as r
import volume_analysis
import options_analysis
import random_var
import datetime
import numpy as np
import pyotp
import time

class stockbot:

    def __init__(self, username, password):
        self.my_holdings = {}
        self.new_buys = {}

    def main(self):
        f.write(str(datetime.datetime.today()) + '\n')
        f.write('-------------\n')
        f.write('Current Account Value: ' + str(r.profiles.load_portfolio_profile()['equity'] + '\n'))
        print('stock_list')
        stock_list = get_stock_list()
        print('buy_list')
        an_list = build_pot_stock_buys(stock_list)
        print('buying')
        to_buy = set_buy_list(an_list)
        f.write("Attempting to buy: " + str(to_buy) + '\n')
        self.new_buys.update(allocate_cash(to_buy)) #buy the stocks we want
        self.my_holdings.update(self.new_buys) # update our holdings
        time.sleep(10) # wait 10 seconds to make sure it goes through
        for stock in self.my_holdings.copy().keys():
            if stock not in r.account.build_holdings().keys():
                del(self.my_holdings[stock]) # check that our list is accurate

        for stock in r.account.build_holdings().keys():
            holdings = r.account.build_holdings()[stock]
            if stock not in self.my_holdings:
                self.my_holdings[stock] = [datetime.datetime.today(), holdings['quantity'], holdings['average_buy_price']]
            if stock in self.my_holdings:
                self.my_holdings[stock][1] = holdings['quantity']
                self.my_holdings[stock][2] = holdings['average_buy_price']

        self.new_buys = {} # new_buys is empty again
        stocks_sold = analyze_holding(self.my_holdings)
        f.write("Stocks sold: " + str(stocks_sold) + '\n')
        for stock in stocks_sold:
            if stock in self.my_holdings.keys():
                del(self.my_holdings[stock])

        f.write("Current Holdings: " + str(self.my_holdings) + '\n')
        f.write('------------\n')
        f.write('\n')




# These functions are not part of the class so no need to call self
def buy_stock(ticker, amount):
    """ Function to execute buy orders """
    dict = r.orders.order_buy_market(ticker, amount, 'gfd')
    f.write("Order for " + ticker + ': ' + str(dict) + '\n')
    if dict != None:
        return datetime.datetime.today() # returns a time stamp for when the stock was bought
    else:
        return False


def sell_stock(ticker, amount):
    """ Function to execute sell orders """
    #try:
    sold = r.orders.order_sell_market(ticker, amount)
    print("Sell Order: " + str(sold))
    return True
    #except Exception as ex:
    #    print("Error in sell_stock()")
    #    print(ex)
    #    return False

def get_stock_list():
    """ Gets a list of stocks to consider buying """
    market_list = []
    top_movers = r.markets.get_top_movers()
    print('top_movers')
    top_100 = r.markets.get_top_100()
    print('top_100')
    top_sp500 = r.markets.get_top_movers_sp500('up')
    print('top_sp500')
    earnings = r.markets.get_all_stocks_from_market_tag('upcoming-earnings')
    market_list += top_movers + top_100 + top_sp500 + earnings
    print(market_list)
    return_list = []
    for stock in market_list:
        if stock['symbol'] not in return_list:
            return_list += [stock['symbol']]
    return return_list

def build_pot_stock_buys(stock_list):
    """ takes a list of stock tickers, and builds a list of stocks that are potential buys """
    analysis_list = []
    fail = 0
    for stock in stock_list:
        try:
            current_price = r.stocks.get_latest_price(stock)[0]
            fundamentals = r.stocks.get_fundamentals(stock)[0] #returns a list for some reason so index element
            volume_average_ratio = float(fundamentals['volume']) / float(fundamentals['average_volume'])
            volume_to_two_week_volume_ratio = float(fundamentals['volume']) / float(fundamentals['average_volume_2_weeks'])
            probabilities = analyze(stock, volume_average_ratio, volume_to_two_week_volume_ratio)
            options_score = options_analysis.options_analysis(stock, current_price)
            monte_carlo_ratio = random_var.get_stock_data(stock)
            analysis_list += [[buy_decision(probabilities, options_score, monte_carlo_ratio), stock]]
        except:
            fail += 1
            pass
    print('length: ', len(stock_list))
    print('fails: ', fail)
    return analysis_list

def buy_decision(probabilities, options_score, monte_carlo_ratio):
    """
    takes probabilities list from the build_pot_stock_buys() function and returns whether
    it's a potential buy or not.
    """
    total = 0
    average_return = probabilities[0]
    volume_prob_high = probabilities[1][0]
    volume_prob_low = probabilities[1][1]
    return_prob_high = probabilities[2][0]
    return_prob_low = probabilities[2][1]

    if average_return > 0:
        total += (1/5)
    else:
        total += 0

    return total + volume_prob_high + (1-volume_prob_low) + return_prob_high + (1-return_prob_low) + options_score - monte_carlo_ratio

def set_buy_list(potential_scores_list):
    buys = []
    while len(buys) <= 10:
        elem_to_add = max(potential_scores_list)
        potential_scores_list.remove(elem_to_add)
        buys += [elem_to_add]

    return buys


def analyze(stock, volume_average_ratio, volume_to_two_week_volume_ratio):
    """
    takes in stock name, avg volume, and 2 week volume to use for analysis
    returns [mean, (pr(high_return), pr(low_return)) x 2] - first tuple volume
    second tuple returns.
    """
    # set up our df,  and lists
    df = volume_analysis.get_historical_data(stock)
    volume_data = volume_analysis.get_volume_data(df)
    volume_average_data = volume_data[0]
    volume_two_week_data = volume_data[1]
    volume_mean = volume_analysis.get_mean(volume_average_data)
    two_week_mean = volume_analysis.get_mean(volume_two_week_data)

    # returns
    returns = volume_analysis.get_returns(df)
    return_mean = volume_analysis.get_mean(returns)

    # tupled list of all three
    volume_and_return_list = volume_analysis.get_ratio_and_volume_list(volume_data[0], volume_data[1], returns)
    volume_probs = volume_analysis.find_volume_probabilities(volume_average_ratio, volume_to_two_week_volume_ratio, volume_and_return_list, return_mean, two_week_mean, volume_mean)
    return_probs = volume_analysis.find_return_probabilities(returns, return_mean)
    return [return_mean, volume_probs, return_probs]


def allocate_cash(buy_list):
    """
    checks how much cash to allocate and whether there is space. Best stocks reported
    first so we always go through them first. If not enough cash, then we don't buy.
    returns a dicitonary of new buys {ticker: [date, amount, price]}
    """
    my_holdings = r.account.build_holdings() # get holdings

    portfolio_cash = None
    user_profile = r.load_account_profile()
    for key, value in user_profile.items():
        if key == 'portfolio_cash':
            portfolio_cash = float(value)
            break
    new_buys = {}
    f.write("Portfolio cash: " + str(portfolio_cash) + '\n')
    for stock in buy_list:
        if stock[1] in my_holdings.keys():
            continue # skip because we already own this stock

        price = float(r.stocks.get_latest_price(stock)[0])

        if float(portfolio_cash) // float(price) < 1:
            continue ## we don't have enough money to trade
        else:
            max_amount_willing = (1/3)*portfolio_cash # willing to give 1/3 of the account to one position
            to_buy = max_amount_willing // price # returns number of shares to buy
            if to_buy >= 1:
                date_bought = buy_stock(stock[1], to_buy)
                if date_bought != False:
                    new_buys[stock[1]] = [date_bought, to_buy, price]
                    portfolio_cash -= to_buy*price
    return new_buys # returns a dict with stock: date, amount, price

def analyze_holding(current_holdings):
    """
    takes in a dictionary of stocks from self.current_holdings and decides whether
    to sell a stock or not. returns a list of sold stocks
    """
    sold = []
    for stock, val in current_holdings.items():
        try:
            df = volume_analysis.get_historical_data(stock)
            returns = volume_analysis.get_returns(df)
            mean_return = volume_analysis.get_mean(returns)
            sd_return = volume_analysis.get_sd(returns)
            sell_score = sell_decision(stock, mean_return, sd_return, float(val[2]))
            print("Sell score for " + str(stock) + ': ' + str(sell_score))
            if sell_score == 1:
                print('Sending sell order for ' + str(stock))
                if sell_stock(stock, float(val[1])):
                    sold += [stock]
        except Exception as ex:
            print("Error with sell order for " + str(stock))
            print(ex)
            pass
    return sold


def sell_decision(stock, mean_return, sd_return, buy_price):

    current_price = float(r.stocks.get_latest_price(stock)[0])

    if ((current_price-buy_price)/buy_price)*100 >= mean_return + sd_return:
        return 1
    elif ((current_price-buy_price)/buy_price)*100 <= mean_return-sd_return:
        return 1
    else:
        return 0




username = #### YOUR USERNMAE HERE ###
password = #### YOUR PASSWORD HERE ###

bot = stockbot(username, password)

while True:
    try:
        start = time.time()
        f = open("LOG.txt", "a")
        totp = pyotp.TOTP("### SET UP PYOTP 2 FACTOR ID HERE ###").now()
        print("Current OTP: ", totp)
        login = r.login(username, password, mfa_code=totp)
        bot.main()
        f.close()
        end = time.time()
        print(end-start)
    except Exception as ex:
        print('There was an error')
        print(ex)
