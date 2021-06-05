from agent.TradingAgent import TradingAgent
import pandas as pd
import numpy as np
import os
from contributed_traders.util import get_file

class valdni_agentLinearReg(TradingAgent):
    """
    Simple Trading Agent that compares the past mid-price observations and places a
    buy limit order if the first window mid-price exponential average >= the second window mid-price exponential average or a
    sell limit order if the first window mid-price exponential average < the second window mid-price exponential average
    """

    def __init__(self, id, name, type, symbol, starting_cash,
                 min_size, max_size, wake_up_freq='60s',
                 log_orders=False, random_state=None):

        super().__init__(id, name, type, starting_cash=starting_cash, log_orders=log_orders, random_state=random_state)
        self.symbol = symbol
        self.min_size = min_size  # Minimum order size
        self.max_size = max_size  # Maximum order size
        self.size = self.random_state.randint(self.min_size, self.max_size)
        self.wake_up_freq = wake_up_freq
        self.mid_list, self.avg_win1_list, self.avg_win2_list = [], [], []
        self.log_orders = log_orders
        self.lookback = 50
        self.trades = []
        self.state = "AWAITING_WAKEUP"

    def kernelStarting(self, startTime):
        super().kernelStarting(startTime)

    def wakeup(self, currentTime):
        """ Agent wakeup is determined by self.wake_up_freq """
        can_trade = super().wakeup(currentTime)
        if not can_trade: return
        self.getLastTrade(self.symbol)
        self.state = "AWAITING_LAST_TRADE"

    def dump_shares(self):
        # get rid of any outstanding shares we have
        if self.symbol in self.holdings and len(self.orders) == 0:
            order_size = self.holdings[self.symbol]
            bid, _, ask, _ = self.getKnownBidAsk(self.symbol)
            if bid:
                self.placeLimitOrder(self.symbol, quantity=order_size, is_buy_order=False, limit_price=0)

    def receiveMessage(self, currentTime, msg):
        """ Momentum agent actions are determined after obtaining the best bid and ask in the LOB """
        super().receiveMessage(currentTime, msg)
        if self.state == "AWAITING_LAST_TRADE" and msg.body['msg'] == "QUERY_LAST_TRADE":
            last = self.last_trade[self.symbol]
            self.trades = (self.trades + [last])[-self.lookback:]
            if len(self.trades) >= self.lookback:
                m,b = np.polyfit(range(len(self.trades)),self.trades,1)
                pred = (self.lookback + 1) * m + b
                holdings = self.getHoldings(self.symbol)
                # bid, _, ask, _ = self.getKnownBidAsk(self.symbol)
                if pred > last:
                    self.placeLimitOrder(self.symbol, quantity=100 - holdings, is_buy_order=True, limit_price=last + 1)
                else:
                    self.placeLimitOrder(self.symbol, quantity=100 + holdings, is_buy_order=False, limit_price=last - 1)
            self.setWakeup(currentTime + pd.Timedelta ("1m"))
            self.state = "AWAITING_WAKEUP"

    def getWakeFrequency(self):
        return pd.Timedelta(self.wake_up_freq)
