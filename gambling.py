import math
import pprint
import datetime

from ib_async import IB, Stock, Option, LimitOrder, Index


#util.startLoop()

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

UNDERLYING_TAG = 'TSLA'
F = 0.1
r = 0.0608
#T = 77/365
#K = 5



#option = Option('RGTI', '20250221', 5, 'C', 'SMART')
underlying = Stock(UNDERLYING_TAG, 'SMART', 'USD')
ib.qualifyContracts(underlying)
ib.sleep(1)

stock_ticker = ib.reqMktData(underlying)
ib.sleep(1)

#contract_details = ib.qualifyContracts(option)
#if contract_details:
#option_ticker = ib.reqMktData(option)
#ib.sleep(2)


#C_bid = option_ticker.bid
#C_ask = option_ticker.ask
#print('index')
#pprint.pprint(dir(stock_ticker))
#print(underlying.conId)
#print(index.conId)
#print('stock')
#pprint.pprint(dir(underlying))
print('AAA')
chains = ib.reqSecDefOptParams(underlying.symbol, '', underlying.secType, underlying.conId)
print(chains[0])
print(dir(chains[0]))
chains = list(filter(lambda x: x.exchange == 'SMART', chains))

#tickers = []
interesting = {}
for chain in chains:
    for expiration in chain.expirations:
        print(expiration)
        #dt = datetime.datetime(int(expiration[:4]), int(expiration[4:6]), int(expiration[6:]))
        #delta = (now - dt).days / 365.0
        interesting[expiration] = {'calls': [], 'puts': []}
        for K in chain.strikes:
            if K < 400.0 or K > 430.0:
                continue
            interesting_call = Option(UNDERLYING_TAG, expiration, K, 'C', 'SMART')
            interesting_put = Option(UNDERLYING_TAG, expiration, K, 'P', 'SMART')
            interesting[expiration]['calls'].append(interesting_call)
            interesting[expiration]['puts'].append(interesting_put)
            # tickers.append(ib.reqMktData)
            # print(f'{K = }; {expiration = }')


ib.sleep(2)
S_bid = stock_ticker.bid
S_ask = stock_ticker.ask
now = datetime.datetime.today()
print('A' * 5)
for expiration, options in interesting.items():
    ib.qualifyContracts(*options['calls'], *options['puts'])
    ib.reqTickers(*options['calls'], *options['puts'])
    dt = datetime.datetime(int(expiration[:4]), int(expiration[4:6]), int(expiration[6:]))
    T = (dt - now).days / 365.0
    good = []
    for call, put in zip(options['calls'], options['puts']):
        #call_ticker = ib.reqMktData(call)
        #put_ticker = ib.reqMktData(put)
        #call_ticker = ib.reqMktData(call, genericTickList='221')
        #put_ticker = ib.reqMktData(put, genericTickList='221')
        # pagal ideja sitie 2 turi buti cachinami ib
        call_ticker = ib.ticker(call)
        put_ticker = ib.ticker(put)
        K = call.strike
        C_ask = call_ticker.ask
        C_bid = call_ticker.bid
        pred_P_ask = C_ask - S_bid + K + F
        pred_P_bid = C_bid - S_ask + K * math.exp(-r * T) - F
        pred_C_ask = P_bid + S_bid - K * math.exp(-r * T) - F
        pred_C_bid = P_ask + S_ask - K * math.exp(-r * T) + F
        P_ask = put_ticker.ask
        P_bid = put_ticker.bid
        if math.isnan(P_bid) or (P_bid + 1) < 0.01:
            continue
        #print(call_ticker)
        #print(put_ticker)
        #print(expiration, K, C_ask, C_bid, P_ask, P_bid)
        #print(f'pred_ask: {pred_P_ask:.2f}', 'real_ask:', P_ask)
        if C_bid > pred_C_bid:
            good.append((C_bid - pred_C_bid, 'CALLSELL', K, expiration, pred_C_bid))
        if C_ask < pred_C_ask:
            good.append((pred_C_ask - C_ask, 'CALLBUY', K, expiration, pred_C_ask))

        # SENI
        if pred_P_ask < P_ask:
            #print(f'Gotaro SELL {K} {expiration} {P_ask = } {pred_P_ask = }')
            good.append((P_ask - pred_P_ask, 'PUTSELL', K, expiration, pred_P_ask))
        if pred_P_bid > P_bid:
            #print(f'Gotaro BUY {K} {expiration} {P_bid = } {pred_P_bid = }')
            good.append((pred_P_bid - P_bid, 'PUTBUY', K, expiration, pred_P_bid))
    if len(good) > 0:
        good.sort(key=lambda x: x[0], reverse=True)
        print('GERIAUSI')
        pprint.pprint(good[:3])
    else:
        print('BLOGIAUSI')


quit()
if None not in [S_bid, S_ask, C_bid, C_ask]:
    # Calculate P_ask and P_bid
    P_ask = C_ask - S_bid + K + F
    P_bid = C_bid - S_ask + K * math.exp(-r * T) - F

    print(P_ask)
    print(P_bid)

    sell_order = LimitOrder('SELL', 1, P_ask)
    buy_order = LimitOrder('BUY', 1, P_bid)

    ib.placeOrder(option, sell_order)
    ib.placeOrder(option, buy_order)
else:
    print('Some market data is missing, ensure subscriptions are active.')

ib.disconnect()
