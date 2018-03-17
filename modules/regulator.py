from typing import Any, Dict, List, NamedTuple, Optional
import collections
import copy
import decimal
import math
import orderbook
import sys
import numpy as np
import pandas as pd

#import modules.arbitrageur
import modules.asset
import modules.misc
import modules.settings as settings



class HistoricExchanges(NamedTuple):
	'''
	Slow traders see different NBBO than fast arbitrageur, we therefore keep the historic snapshot of the exchanges in
	order to show them the 'correct' NBBO based on the NBBO delay.
	'''
	exchanges: Dict[str, orderbook.orderbook.NonUniqueIdOrderBook]
	timestamp: float



class Regulator:
	def __init__(self, national_best_bid_and_offer_delay: float, asset: modules.asset.Asset, batch_auction_length: int = settings.BATCH_AUCTION_LENGTH) -> None:
		self.national_best_bid_and_offer_delay = national_best_bid_and_offer_delay
		self.accurate_national_best_bid_and_offer: modules.misc.NBBO = modules.misc.NBBO(None, None, None, None)
		self.asset = asset
		self.batch_auction_length = batch_auction_length
		self.exchanges: Dict[str, orderbook.orderbook.NonUniqueIdOrderBook] = {
			exchange_name: orderbook.orderbook.NonUniqueIdOrderBook()
			for exchange_name in settings.NAMES_OF_EXCHANGES
		}
		self.historic_exchanges_list: List[HistoricExchanges] = [
			HistoricExchanges(
				exchanges = self.exchanges,
				timestamp = 0
			)
		]
		self.current_time = 0
		# Once trader's order is executed, we keep track of it in the execution_times list, in the end we take a mean
		# of the time it took for a resting order to be executed.
		self.execution_times: List[float] = []
		self.last_order_idx: Dict[str, int] = {'bid': 0, 'ask': 0}
		# Meta will hold information about the trader who is behind the order, as well about the times the order
		# was added into the orderbook and later executed.
		self.meta: Dict[order_executed_by_zerointelligence.misc.LimitOrder, Dict[str, Any]] = {}
		if self.batch_auction_length:
			self.clearing_times = self.generate_batch_auction_clearing_times(self.batch_auction_length)
		else: 
			self.clearing_times = pd.Series()
		self.add_current_exchanges_to_historic_exchanges()
		self.list_orders_to_be_processed: List[modules.misc.TraderOrderIdx] = []


	def generate_batch_auction_clearing_times(self, batch_auction_length: int) -> pd.Series:
		'''
		Batch auction of length 0 means continuous trading.
		'''
		entries = list(np.cumsum([batch_auction_length] * int(settings.SESSION_LENGTH / batch_auction_length)))
		return pd.Series(
			index = entries,
			data = self			
		)



	def process_order(self, side: int, order_price: int, exchange_name: str) -> modules.misc.ExchangeResponse:
		'''
		The order comes in and we need to decide, whether it will be executed or added to the orderbook.
		This order has already been routed by the trader, therefore the exchange is fixed, price is fixed, the only
		thing that matters is whether the order is executed immediately or not.
		There are three cases which can occur. The trade is executed at predetermined price, or it is executed at an even
		better price. Finally it can be added to the orderbook at the initial price.
		'''
		side_type = modules.misc.side_to_orderbook_type(not side)
		action = 'A'
		try:
			best_price = self.exchanges[exchange_name].get_side(side_type).get_best().price
		except orderbook.exceptions.OrderSideEmpty:
			best_price = None

		if best_price and ((side and best_price <= order_price) or (not side and best_price >= order_price)):
			order_price = best_price
			action = 'E'
		return modules.misc.ExchangeResponse(action, order_price)


	def copy_all_orders_from_one_exchange_to_another(self, old_exchange: orderbook.orderbook.NonUniqueIdOrderBook) -> orderbook.orderbook.NonUniqueIdOrderBook:
		new_exchange = orderbook.orderbook.NonUniqueIdOrderBook()
		for side in (orderbook.types.OrderSide.ASK, orderbook.types.OrderSide.BID):
			orders = old_exchange.get_side(side).__iter__()
			while True:
				try:
					new_exchange.add_order(**self.convert_order_to_dictionary(next(orders)))
				except StopIteration:
					break
		return new_exchange


	@staticmethod
	def convert_order_to_dictionary(order):
		return {
			'side': order.side,
			'order_id': order.id,
			'price': order.price,
			'quantity': order.quantity,
			'position': None,
			'metadata': order.metadata
		}


	def add_current_exchanges_to_historic_exchanges(self) -> None:
		'''
		We insert the new element at the top of the list, as while iterating through the list we can then make a cutoff once
		we find an old enough (older than settings.NATIONAL_BEST_BID_AND_OFFER_DELAY) historic snapshot of the exchanges.
		'''
		new_exchanges = {
			exchange_name: self.copy_all_orders_from_one_exchange_to_another(exchange)
			for exchange_name, exchange in self.exchanges.items()
		}
		self.historic_exchanges_list.insert(0, 
			HistoricExchanges(
				exchanges = new_exchanges,
				timestamp = self.current_time
			)
		)


	def remove_redundant_historic_exchanges(self) -> None:
		'''
		The :national_best_bid_and_offer_delay: sets the maximum delay, therefore we can delete historic snapshot of exchanges
		which are older than the first exchange which is older than :params national_best_bid_and_offer_delay:.
		We can then refer to the information which slow traders see simply as the last element of :params self.historic_exchanges_list:.
		'''
		for idx, historic_exchange in enumerate(self.historic_exchanges_list):
			if self.current_time - self.national_best_bid_and_offer_delay >= historic_exchange.timestamp:
				self.historic_exchanges_list = self.historic_exchanges_list[:max(idx, 1)]
				return


	def do(self) -> List:
		'''
		The do function is called only in case of the batch auction, as these require period actions from the Regulator.
		It gathers all orders which were submitted during the batch interval and processes them accordingly.
		'''
		orders_dataframe = self.generate_orders_dataframe()
		list_regulator_responses_orderbook = self.add_batch_of_orders_into_orderbook(orders_dataframe)
		exchange_information = self.get_orders_to_be_cleared()
		if exchange_information:
			self.clear_orders_in_batch_auction(exchange_information)
		return []



	def generate_orders_dataframe(self) -> Optional[pd.DataFrame]:
		if self.list_orders_to_be_processed:
			list_of_orders_dict = []
			for idx, timestamp, order in self.list_orders_to_be_processed:
				order = order._asdict()
				order.update({'trader_idx': idx, 'timestamp': timestamp})
				list_of_orders_dict.append(order)
			orders_dataframe = pd.DataFrame.from_dict(list_of_orders_dict)
			orders_dataframe['random_seed'] = np.random.permutation(len(orders_dataframe.index))
			orders_dataframe.sort_values(['side', 'limit_price', 'random_seed'], inplace = True)
			del orders_dataframe['random_seed']
			self.list_orders_to_be_processed = []
			return self.filter_orders_dataframe_by_highest_timestamp(orders_dataframe)
		return None


	@staticmethod
	def filter_orders_dataframe_by_highest_timestamp(orders_dataframe: pd.DataFrame) -> pd.DataFrame:
		'''
		If a trader submits multiple orders during the batch auction, we only take account of the latest one.
		It is the same as if he deleted the order every time he submitted a new one.
		'''
		max_timestamp_per_trader = orders_dataframe.groupby('trader_idx')['timestamp'].max().reset_index()
		max_timestamp_per_trader['is_maximum_timestamp'] = True
		orders_dataframe = orders_dataframe.join(max_timestamp_per_trader['is_maximum_timestamp'])
		orders_dataframe['is_maximum_timestamp'] = orders_dataframe['is_maximum_timestamp'].fillna(False)
		orders_dataframe = orders_dataframe[orders_dataframe['is_maximum_timestamp']]
		del orders_dataframe['is_maximum_timestamp']
		return orders_dataframe


	def add_batch_of_orders_into_orderbook(self, orders_dataframe: pd.DataFrame) ->  List[modules.misc.ExchangeResponse]:
		list_regulator_responses: List[modules.misc.ExchangeResponse] = []
		for exchange_name in self.exchanges:
			exchange_dataframe = orders_dataframe[orders_dataframe['exchange_name'] == exchange_name]
			for row in range(len(exchange_dataframe)):
				dataframe_row = exchange_dataframe.iloc[row]
				list_regulator_responses.append(self.add_limit_order(dataframe_row = dataframe_row))
		return list_regulator_responses


	def get_orders_to_be_cleared(self) -> int:
		'''
		We will sort orders by their order in the bid and ask queues in decreasing and increasing orders respectively.
		Then by comparing their prices, we will see whether they will clear or not.
		'''
		exchange_information: Dict[str, Any] = {}
		for exchange_name in self.exchanges:
			list_orders_to_be_cleared: List[orderbook.types.Order] = []
			bid_orders = list(self.exchanges[exchange_name].bid)
			ask_orders = list(self.exchanges[exchange_name].ask)
			highest_ask_price, lowest_bid_price = None, None
			for order in range(min(len(bid_orders), len(ask_orders))):
				if bid_orders[order].price >= ask_orders[order].price:
					highest_ask_price = ask_orders[order].price
					lowest_bid_price = bid_orders[order].price
					for limit_order in (bid_orders[order], ask_orders[order]):
						list_orders_to_be_cleared.append(limit_order)
					continue
				if highest_ask_price and lowest_bid_price:
					exchange_information[exchange_name] = (
						int((highest_ask_price + lowest_bid_price) / 2),
						list_orders_to_be_cleared
					)
				break
		return exchange_information


	def clear_orders_in_batch_auction(self, exchange_information: Dict[str, Any]) -> None:
		list_executed_traders: List[modules.misc.TraderOrderIdx] = []
		for exchange_name in exchange_information:
			clearing_price, list_orders_to_be_cleared = exchange_information[exchange_name]
			for limit_order in list_orders_to_be_cleared:
				list_executed_traders.append(
					self.execute_order(
						exchange_name = exchange_name,
						limit_order = limit_order
					)
				)



	def clear_orders_in_continuous_auction(self) -> None:
		pass


	def increase_last_order_idx(self, side: str) -> int:
		'''
		This function both increases the last order idx count and returns the idx, so that it can be used immediately.
		'''
		self.last_order_idx[side] += 1
		return self.last_order_idx[side]


	def add_limit_order(self, dataframe_row: pd.DataFrame) -> None:
		''''
		The function updates the number of last order on the market as a whole. This ensures uniqueness of the id per
		side on all exchanges. It then assigns the order and exchange to the Trader class for future reference.
		Finally it submits the order onto the appropriate exchange.
		'''
		order_idx = self.increase_last_order_idx(modules.misc.side_to_string(dataframe_row['side']))
		new_order = modules.misc.LimitOrder(
			idx = order_idx,
			side = modules.misc.side_to_orderbook_type(dataframe_row['side']),
			exchange_name = dataframe_row['exchange_name']
		)
		nanoseconds, seconds = math.modf(dataframe_row['timestamp'])
		self.meta[new_order] = {
			'trader_idx': dataframe_row['trader_idx'],
			'time_entry': dataframe_row['timestamp'],
		}
		self.exchanges[dataframe_row['exchange_name']].add_order(
			side = modules.misc.side_to_orderbook_type(dataframe_row['side']),
			order_id = order_idx,
			price = dataframe_row['limit_price'],
			quantity = 1,
			position = None,
			metadata = {
				'timestamp': seconds * int(1e9) + nanoseconds * int(1e18)
			}
		)
		return modules.misc.TraderOrderIdx(
			trader_idx = dataframe_row['trader_idx'],
			timestamp = dataframe_row['timestamp'],
			order = new_order
		)


	def execute_order(self, exchange_name: str, limit_order: orderbook.types.Order) -> int:
		'''
		
		'''
		self.exchanges[exchange_name].fill_order(
			order_id = limit_order.id,
			filled_quantity = 1,
			side = limit_order.side
		)
		# We have to keep track of the trader who initially submitted the order onto the exchange.

		passive_side_order = modules.misc.LimitOrder(
			idx = limit_order.id,
			side = limit_order.side,
			exchange_name = exchange_name
		)

		trader_with_passive_limit_order = self.meta[passive_side_order]
		self.execution_times.append(self.current_time - trader_with_passive_limit_order['time_entry'])
		# self.update_position_and_trades(
		# 	order = modules.misc.LimitOrder(best_order.id, self.side, best_order.price, exchange_name)
		# )
		return [modules.misc.TraderOrderIdx(
			trader_idx = trader_with_passive_limit_order['trader_idx'],
			order = passive_side_order,
			timestamp = self.current_time
		)]