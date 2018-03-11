from typing import Dict, List, Optional, Tuple
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
	def __init__(self, exchange_name: str, number_of_orders: int,
	ticks_between_orders: int, spread_around_asset: int, *args, **kwargs) -> None:
		super(MarketMaker, self).__init__(*args, **kwargs)
		self.exchange_name = exchange_name
		self.number_of_orders = number_of_orders
		self.ticks_between_orders = ticks_between_orders
		self.spread_around_asset = spread_around_asset


	def do(self) -> Dict:
		'''
		Trade function calls all the functions which are necessary for the trader to trade.
		'''
		highest_bid, lowest_ask = self.get_central_ladder_prices()
		ladder_bids, ladder_asks = self.generate_order_ladders(
			highest_bid = highest_bid,
			lowest_ask = lowest_ask
		)
		trimmed_ladder_bids, trimmed_ladder_asks = self.trim_orders_ladder(
			ladder_bids = ladder_bids,
			ladder_asks = ladder_asks
		)
		if self.current_orders:
			for order in self.current_orders:
				self.delete_order_from_an_exchange(
					order = order,
					exchange_name = order.exchange_name,
					exchanges = self.regulator.exchanges,
				)
		self.current_orders = []

		list_trader_order_tuple = []
		
		for side, order_prices in enumerate([trimmed_ladder_asks, trimmed_ladder_bids]):
			for order_price in order_prices:
				response = self.send_order_to_the_exchange(side, order_price)
				self.side = side
				list_trader_order_tuple = list_trader_order_tuple + self.process_exchange_response(
					**response._asdict(),
					exchange_name = self.exchange_name
				)
		return list_trader_order_tuple


	def get_central_ladder_prices(self) -> Tuple[List[Optional[int]], List[Optional[int]]]:
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
		Generates symmetric ladder around the central ladder prices.
		'''
		return tuple([
				central_ladder_price + direction * settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS * count
				for count in range(settings.MARKET_MAKER_NUMBER_ORDERS)
				if central_ladder_price + direction * settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS * count > 0
			]
			for central_ladder_price, direction in ((highest_bid, -1), (lowest_ask, 1)) 
		)


	def trim_orders_ladder(self, ladder_bids: List[Optional[int]], ladder_asks: List[Optional[int]]) -> Tuple[List[Optional[int]], List[Optional[int]]]:
		'''
		Looks at the (possibly lagged) value of NBBO and removes orders, which would be executed immediately against resting orders.
		'''
		national_best_bid_and_offer = self.get_national_best_bid_and_offer()
		trimmed_ladder_bids, trimmed_ladder_asks = ladder_bids, ladder_asks
		if national_best_bid_and_offer.bid:
			trimmed_ladder_asks = [int(ask) for ask in trimmed_ladder_asks if ask > national_best_bid_and_offer.bid]
		if national_best_bid_and_offer.ask:
			trimmed_ladder_bids = [int(bid) for bid in trimmed_ladder_bids if bid < national_best_bid_and_offer.ask]
		return (trimmed_ladder_bids, trimmed_ladder_asks)


	def send_order_to_the_exchange(self, side: int, limit_price: int) -> List:
		'''
		We get back the info from the exchange (wrapped in the ExchangeResponse object), saying whether our order was executed or added to the orderbook.
		'''
		return self.regulator.process_order(
			side = side,
			order_price = limit_price,
			exchange_name = self.exchange_name,
		)



	def calculate_total_surplus(self) -> int:
		'''
		At the end of trading this function sums the total payoff which consists of the closed trades (Profit or Loss)
		and of the open position, valued at the current price, adjusted for private benefits.
		'''
		payoff = self.calculate_profit_from_trading()
		payoff += self.calculate_value_of_final_position()
		return payoff
