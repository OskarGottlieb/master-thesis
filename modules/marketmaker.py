from typing import List, Optional, Tuple
import decimal
import math

import numpy as np
import pandas as pd

import modules.settings as settings
import modules.trader



class MarketMaker(modules.trader.Trader):
	'''
	MarketMaker is a type of trader who only submits limit orders and cancels any which he perceives might be
	executed on the spot. He does not have a private valuation for the asset.
	'''
	def __init__(self, default_exchange: str, number_of_orders: int,
	ticks_between_orders: int, spread_around_asset: int, *args, **kwargs) -> None:
		super(MarketMaker, self).__init__(*args, **kwargs)
		self.default_exchange = default_exchange
		self.number_of_orders = number_of_orders
		self.ticks_between_orders = ticks_between_orders
		self.spread_around_asset = spread_around_asset


	def trade(self):
		'''
		Trade function calls all the functions which are necessary for the trader to trade.
		'''
		highest_bid, lowest_ask = self.get_central_ladder_prices()
		
		return {}


	def get_central_ladder_prices(self):
		'''
		Based on the estimate of the asset price, we generate bid and ask basis prices for the ladder of orders.
		'''
		price_estimate = self.get_estimate_of_the_fundamental_value_of_the_asset()
		return tuple(
			max(price_estimate + 0.5 * offset, 0)
			for offset in (- settings.MARKET_MAKER_SPREAD_AROUND_ASSET, settings.MARKET_MAKER_SPREAD_AROUND_ASSET)
		)


	def generate_order_ladders(self, highest_bid: int, lowest_ask: int) -> Tuple[List[int], List[int]]:
		'''

		'''
		pass