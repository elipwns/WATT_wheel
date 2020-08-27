import robin_stocks as rs
import pyotp
import math
import calendar
import os
from datetime import datetime, timedelta, date

#set to True to only output what would have been done, but not actually go through with any trades.
dry_run = True

#keep this variable the same as (or less than) the amount you are automatically transfering from bank to robinhood each period
amount_per_period = 40
stock_symbol = "WATT"
log_filename = "logs/" + str(date.today()) + ".txt"
#login to robinhood, only need to to totp once it seems, would need to add TOTP as third param to login.
#totp = pyotp.TOTP(os.environ.get('TOTP')).now()
login = rs.login(os.environ.get('EMAIL'), os.environ.get('PASSWORD'))

#check cash balance, store as variable
buying_power = rs.profiles.load_account_profile(info="buying_power")
print("buying_power: $" + buying_power)
f = open(log_filename, "a")
f.write("Starting buying power = $" + buying_power+ '\n')
f.close()

#check latest price of stock we interested in
latest_price = rs.stocks.get_latest_price(stock_symbol)
#add in some wiggle room, 2 cents
wiggle_room_price = float(latest_price[0]) + 0.02

#options date for WATT is always 3rd friday of the month
#first find what today is
now = datetime.now()
#then find what the 3rd friday is of next month
first_day_of_next_month = datetime(now.year, now.month + 1, 1)
first_friday_of_next_month = first_day_of_next_month + timedelta(days=((4-calendar.monthrange(now.year,now.month+1)[0])+7)%7)
third_friday_of_next_month = first_friday_of_next_month + timedelta(days=14)
#convert date into YYYY-MM-DD format
mday = "0"
day = third_friday_of_next_month.day
if day < 10:
    mday = mday + str(day)
else:
    mday = str(day)

m_month = "0"
month = third_friday_of_next_month.month
if month < 10:
    m_month = m_month + str(month)
else:
    m_month = str(month)

exp_date = str(third_friday_of_next_month.year) + "-" + m_month + "-" + mday

#if buying_power >= 100 * share price, i can sell a cash covered put
#need to check if i already have sold one, possibility can afford to sell another one, but need to check and such
#else amass more shares / moneys first
if float(buying_power) >= (100 * wiggle_room_price):
    quantity = math.floor(float(buying_power) / (100 * wiggle_room_price))
    strikes = rs.options.find_options_by_specific_profitability(stock_symbol, exp_date, None, 'put', 'chance_of_profit_short', 0.70, 0.80, 'strike_price')
    prices = rs.options.find_options_by_specific_profitability(stock_symbol, exp_date, None, 'put', 'chance_of_profit_short', 0.70, 0.80, 'last_trade_price')
    if dry_run:
        print("Would have attempted to sell " + quantity + " cash covered put option(s) at a strike of " + strikes[0] + " for a profit of $" + prices[0] + " per contract.")
    else:
        ret = rs.orders.order_sell_option_limit("open", "credit", float(prices[0]), stock_symbol, quantity, exp_date, float(strikes[0]), 'put', 'gfd')

        #send a text message to me with outcome, either how many bought or what went wrong if possible.
        for item in ret:
            print(item.items())

        #if i order something i should probably then recheck how much buying power i have
        buying_power = rs.profiles.load_account_profile(info="buying_power")


#if current balance >= amount i want to buy each time period, should be auto depositing this amount or more per time period
if float(buying_power) >= amount_per_period:
    #calculate how many shares can afford currently
    shares_can_afford = math.floor(amount_per_period / wiggle_room_price)
    if dry_run:
        print("Would have tried to buy " + shares_can_afford + " " + stock_symbol + " at $" + wiggle_room_price + " per share or less.")
    else:
        #limit order - set to market price + a lil, during market hours, good for today, number of shares
        ret = rs.orders.order_buy_limit(stock_symbol, shares_can_afford, wiggle_room_price, timeInForce="gfd")

        #send a text message to me with outcome, either how many bought or what went wrong if possible.
        for item in ret:
            print(item.items())

        #if i order something i should probably then recheck how much buying power i have
        buying_power = rs.profiles.load_account_profile(info="buying_power")

else:
    #send a text message with a message saying i didnt have enough buying power to cover amount i want to invest per period
    print("Did Not buy more shares. Current buying power is: $" + buying_power + " , and current requested investment amount is: $" + str(amount_per_period))
    f = open(log_filename, "a")
    f.write("Did not buy more shares. Current buying power is: $" + buying_power + " , and current requested investment amount is: $" + str(amount_per_period)+ '\n')
    f.close()

#check how many shares I have of the stock we working with
#if i have >= 100 shares I can start selling covered calls
print("number of WATT shares owned: ")
num_shares_owned = rs.account.build_holdings()[stock_symbol]['quantity']
print(num_shares_owned)
f = open(log_filename, "a")
f.write("Number of WATT shared currently owned: " + num_shares_owned+ '\n')
f.close()

if float(num_shares_owned) >= 100:
    quantity = math.floor(num_shares_owned / 100)
    #using the desired exp date and chance of profit range, we can find an option to sell. need to find a good strike and price for the option

    strikes = rs.options.find_options_by_specific_profitability(stock_symbol, exp_date, None, 'call', 'chance_of_profit_short', 0.75, 0.80, 'strike_price')
    prices = rs.options.find_options_by_specific_profitability(stock_symbol, exp_date, None, 'call', 'chance_of_profit_short', 0.75, 0.80, 'last_trade_price')
    if dry_run:
        print("Would have tried to sell " + quantity + " covered call option expiring on " + exp_date + " with a strike price of $" + strikes[0] + " for an instant profit of $" + prices[0])
    else:
        #do order
        ret = rs.orders.order_sell_option_limit("open", "credit", float(prices[0]), stock_symbol, quantity, exp_date, float(strikes[0]), 'call', 'gfd')

        #send a text message to me with outcome, either how many bought or what went wrong if possible.
        for item in ret:
            print(item.items())

else:
    print("Not enough shares to sell a covered call.")
    f = open(log_filename, "a")
    f.write("Not enough shares to sell covered calls currently."+ '\n')
    f.close()


# if this script ran everyday at 7am or w/e for example, and then it created a file with what it did / didnt do. 
# Was market open? What's my starting / ending balance after script is done doing stuff
# Just log any actions it takes into a new file with todays date in a folder for reccord keeps.

f = open(log_filename, "a")
f.write("----------------------------------------------------------------------------"+ '\n\n')
f.close()