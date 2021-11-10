import asyncio
from binance.streams import BinanceSocketManager
from binance.client import  Client
import numpy as np
import pandas as pd

api_key = '' #valid API_Key needed here
api_secret = '' #valid API_secret needed here
client = Client(api_key,api_secret)

#  two MAs
Short_term = 7
Long_term = 25

#  sum of previous price values for the particular symbol is calculated except live value
def gethistorials(symbol, Long_term):
    df = pd.DataFrame(client.get_historical_klines(symbol,'1d',str(Long_term) + 'days ago UTC', '1 day ago UTC'))
    closes = pd.DataFrame(df[4])
    closes.columns = ['Close']
    closes['Short_term'] = closes.Close.rolling(Short_term - 1).sum()
    closes['Long_term'] = closes.Close.rolling(Long_term - 1).sum()
    closes.dropna(inplace = True)
    return closes


historicals = gethistorials('BTCUSDT', Long_term)
#print(historicals)

#average of short term and long term values are calculated including live prices

def liveSMA(hist,live):
    liveST = (hist['Short_term'].values + live.Price.values) / Short_term
    liveLT = (hist['Long_term'].values + live.Price.values) / Long_term

    return liveST, liveLT


#this function takes messages from binanace nad translating into some readable data -data we can calculate with

def createFrame(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:,['s','E','p']]
    df.columns = ['symbol','Time','price']
    df.Price = df.price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit = 'ms')
    return df


#crossover
async def main(coin, qty, SL_limit, open_position = False):
    bm = BinanceSocketManager(client)
    ts = bm.trade_socket(coin)
    async with ts as tscm:
        while True:
            #res - message from websocket
            res = await tscm.recv()
            if res:
                frame = createFrame(res)
                print(frame)
                liveST, liveLT = liveSMA(historicals, frame)
                #if short term  greater than long -term total values or not
                if liveST > liveLT and not open_position:
                    order = client.create_order(symbol = coin, side = 'BUY', type = 'MARKET',quantity = qty)
                    #print(order)
                    print('buy')

                    buy_price = float(order['fills'][0]['price'])
                    open_position = True

                if open_position:
                    # and vice-versa
                    if frame.Price[0] < buy_price * SL_limit or frame.price[0] > 1.02 * buy_price:
                        order = client.create_order(symbol = coin,side = 'SELL', type = 'MARKET', quantity = qty)
                        #print(order)
                        print('sell')

                        loop.stop()





if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main('BTCUSDT',100, 0.98))











