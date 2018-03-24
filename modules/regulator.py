from typing import Any, Dict, List, NamedTuple, Optional, Tuple
import collections
import copy
import decimal
import math
import logwood
import orderbook
import sys
import numpy as np
import pandas as pd

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
		self.logger = logwood.get_logger(f'{self.__class__.__name__}')
		self.national_best_bid_and_offer_delay = national_best_bid_and_offer_delay
		self.asset = asset
		self.batch_auction_length = batch_auction_length
		self.continuous_trading = False if batch_auction_length else True
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
		self.last_clearing_time: int = 0
		# Once trader's order is executed, we keep track of it in the execution_times list, in the end we take a mean
		# of the time it took for a resting order to be executed.
		self.execution_times: List[float] = []
		self.last_order_idx: Dict[str, int] = {'bid': 0, 'ask': 0}
		# Meta will hold information about the trader who is behind the order, as well about the times the order
		# was added into the orderbook and later executed.
		self.meta: Dict[order_executed_by_zerointelligence.misc.LimitOrder, Dict[str, Any]] = {}
		if not self.continuous_trading:
			self.clearing_times = self.generate_batch_auction_clearing_times()
		else: 
			self.clearing_times = pd.Series()
		self.add_current_exchanges_to_historic_exchanges()
		self.dict_orders_to_be_processed: Dict[modules.misc.Order: modules.misc.TraderTimestamp] = {}
		self.dict_regulator_responses_additions: Dict[modules.misc.LimitOrder: modules.misc.TraderTimestamp] = {}
		self.dict_regulator_responses_executions: Dict[modules.misc.Order: modules.misc.TraderTimestamp] = {}
		self.dict_prices_of_executed_orders: Dict[modules.misc.Order: int] = {}
		self.clearing_price: Dict[str, int] = {}
		self.list_market_information: List[modules.misc.MarketInfo] = []
		self.total_number_of_trades: int = 0


	def generate_batch_auction_clearing_times(self) -> pd.Series:
		'''
		Batch auction of length 0 means continuous trading.
		'''
		entries = list(np.cumsum([self.batch_auction_length] * int(settings.SESSION_LENGTH / self.batch_auction_length)))
		return pd.Series(
			index = entries,
			data = self			
		)


	def reset_regulator_information(self) -> None:
		self.clearing_price: Dict[str, int] = {}
		self.dict_regulator_responses_additions: Dict[modules.misc.LimitOrder: modules.misc.TraderTimestamp] = {}
		self.dict_regulator_responses_executions: Dict[modules.misc.Order: modules.misc.TraderTimestamp] = {}
		self.dict_prices_of_executed_orders: Dict[modules.misc.Order: int] = {}


	def process_order(self, order: modules.misc.Order, trader_timestamp: modules.misc.TraderTimestamp) -> None:
		'''
		Only called in continuous trading.

		The order comes in and we need to decide, whether it will be executed or added to the orderbook.
		This order has already been routed by the trader, therefore the exchange is fixed, limit price is given, the only
		thing that matters is whether the order is executed immediately or not.
		There are three cases which can occur. The trade is executed at predetermined price, or it is executed at an even
		better price. Finally it can be added to the orderbook at the initial price.
		'''
		side_type = modules.misc.side_to_orderbook_type(not order.side)
		action = 'A'
		try:
			best_order = self.exchanges[order.exchange_name].get_side(side_type).get_best()
			best_price = best_order.price
			limit_order_passive = self.orderbook_type_order_to_limit_order(order.exchange_name, best_order)
			limit_order_active = self.orderbook_type_order_to_limit_order(order.exchange_name, best_order, True)
		except orderbook.exceptions.OrderSideEmpty:
			best_price = None

		if best_price and ((order.side and best_price <= order.limit_price) or (not order.side and best_price >= order.limit_price)):
			self.logger.info(f'Trader {trader_timestamp.trader_idx} is actively hiting trader\'s {self.meta[limit_order_passive].trader_idx} order on exchange {order.exchange_name} at price {best_price}')			
			self.meta[limit_order_active] = trader_timestamp
			self.asset.asset_price_series[self.current_time] = best_price
			self.dict_prices_of_executed_orders.update(
				{limit_order_passive: best_price, limit_order_active: best_price}
			)
			# We first add the passive side of the execution and then the active one.
			self.dict_regulator_responses_executions.update(
				self.execute_order(
					exchange_name = order.exchange_name,
					limit_order = limit_order_passive,
				)
			)
			self.dict_regulator_responses_executions.update(
				self.execute_order(
					exchange_name = order.exchange_name,
					limit_order = limit_order_active,
					active_hit = True
				)
			)
		else:
			self.dict_regulator_responses_additions.update(
				self.add_limit_order(
					exchange_name = order.exchange_name,
					side = order.side,
					limit_price = order.limit_price,
					trader_idx = trader_timestamp.trader_idx,
					timestamp = trader_timestamp.timestamp
				)
			)


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


	def do(self) -> None:
		'''
		The do function is called only in case of the batch auction, as these require period actions from the Regulator.
		It gathers all orders which were submitted during the batch interval and processes them accordingly.
		'''
		self.last_clearing_time = self.current_time
		orders_dataframe = self.generate_orders_dataframe()
		self.add_batch_of_orders_into_orderbook(orders_dataframe)
		dict_exchanges_orders_to_be_cleared = self.get_orders_to_be_cleared()
		if dict_exchanges_orders_to_be_cleared:
			self.clear_orders_in_batch_auction(dict_exchanges_orders_to_be_cleared)
			self.logger.info('Cleared the market in a batch auction.')


	def generate_orders_dataframe(self) -> Optional[pd.DataFrame]:
		if self.dict_orders_to_be_processed:
			list_of_dict_orders: List[Dict[str, Any]] = []
			for order, trader_timestamp in self.dict_orders_to_be_processed.items():
				order = order._asdict()
				order.update({'trader_idx': trader_timestamp.trader_idx, 'timestamp': trader_timestamp.timestamp})
				list_of_dict_orders.append(order)
			orders_dataframe = pd.DataFrame.from_dict(list_of_dict_orders)
			orders_dataframe['random_seed'] = np.random.permutation(len(orders_dataframe.index))
			orders_dataframe.sort_values(['side', 'limit_price', 'random_seed'], inplace = True)
			del orders_dataframe['random_seed']
			self.dict_orders_to_be_processed = {}
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


	def add_batch_of_orders_into_orderbook(self, orders_dataframe: pd.DataFrame) -> None:
		'''
		Processes the :params orders_dataframe: and adds all orders as limit orders into the respective orderbook.
		'''
		for exchange_name in self.exchanges:
			exchange_dataframe = orders_dataframe[orders_dataframe['exchange_name'] == exchange_name]
			for row in range(len(exchange_dataframe)):
				dataframe_row = exchange_dataframe.iloc[row]
				self.dict_regulator_responses_additions.update(self.add_limit_order(**dataframe_row.to_dict()))


	def get_orders_to_be_cleared(self) -> int:
		'''
		We will sort orders by their order in the bid and ask queues in decreasing and increasing orders respectively.
		Then by comparing their prices, we will see whether they will clear or not.
		Also if the order being executed has been just added to the orderbook during the last batch auction, we will
		delete this order from :params :
		'''
		dict_exchanges_orders_to_be_cleared: Dict[str, orderbook.types.Order] = collections.defaultdict(list)
		for exchange_name in self.exchanges:
			bid_orders = list(self.exchanges[exchange_name].bid)
			ask_orders = list(self.exchanges[exchange_name].ask)
			highest_ask_price, lowest_bid_price = None, None
			for order in range(min(len(bid_orders), len(ask_orders))):
				if bid_orders[order].price >= ask_orders[order].price:
					highest_ask_price = ask_orders[order].price
					lowest_bid_price = bid_orders[order].price
					trader_bid = self.meta[self.orderbook_type_order_to_limit_order(exchange_name, bid_orders[order])]
					trader_ask = self.meta[self.orderbook_type_order_to_limit_order(exchange_name, ask_orders[order])]
					for executed_order in (bid_orders[order], ask_orders[order]):
						self.remove_executed_order_from_dict_of_additions(exchange_name, executed_order)
						dict_exchanges_orders_to_be_cleared[exchange_name].append(
							executed_order
						)
					self.logger.info(f'The {exchange_name} exchange cleared order {bid_orders[order].id} of trader {trader_bid.trader_idx} and {ask_orders[order].id} of {trader_ask.trader_idx}.') 
					continue
				break
			if highest_ask_price and lowest_bid_price:
				self.clearing_price[exchange_name] = int((highest_ask_price + lowest_bid_price) / 2)
				self.logger.info(f'The clearing price at {exchange_name} is {self.clearing_price[exchange_name]}.')
				self.exchange_price_series[exchange_name][self.current_time] = self.clearing_price[exchange_name]
		return dict_exchanges_orders_to_be_cleared


	def clear_orders_in_batch_auction(self, dict_exchanges_orders_to_be_cleared: Dict[str, List[orderbook.types.Order]]) -> None:
		for exchange_name in dict_exchanges_orders_to_be_cleared:
			for limit_order in dict_exchanges_orders_to_be_cleared[exchange_name]:
				self.dict_regulator_responses_executions.update(
					self.execute_order(
						exchange_name = exchange_name,
						limit_order = self.orderbook_type_order_to_limit_order(exchange_name, limit_order)
					)
				)
		

	def remove_executed_order_from_dict_of_additions(self, exchange_name: str, order: orderbook.types.Order) -> None:
		'''
		If an order is added into the orderbook and executed during the same batch auction, we need to remove this
		order from the additions dictionary, as otherwise the trade would be recorded as both an addition and an execution.
		'''
		limit_order = self.orderbook_type_order_to_limit_order(
			exchange_name = exchange_name,
			order = order
		)
		if limit_order in self.dict_regulator_responses_additions:
			del self.dict_regulator_responses_additions[limit_order]


	def orderbook_type_order_to_limit_order(self, exchange_name: str, order: orderbook.types.Order, reverse_side: bool = False) -> modules.misc.LimitOrder:
		side = order.side
		order_id = order.id
		if reverse_side:
			side = orderbook.OrderSide.BID if order.side == orderbook.OrderSide.ASK else orderbook.OrderSide.ASK
			order_id = self.increase_last_order_idx(modules.misc.side_orderbook_type_to_string(side))
		
		return modules.misc.LimitOrder(
			idx = order_id,
			side = side,
			exchange_name = exchange_name
		)


	def clear_orders_in_continuous_auction(self) -> None:
		'''
		Proceeses the dict of orders which should contain links to one trader only!
		'''
		if self.dict_orders_to_be_processed:
			assert len(set(self.dict_orders_to_be_processed.values())) == 1, self.logger.error(
				'The regulator is trying to process more than one order per timestamp.'
			)
			for order in self.dict_orders_to_be_processed:
				self.process_order(
					order = order,
					trader_timestamp = self.dict_orders_to_be_processed[order]
				)

		self.dict_orders_to_be_processed = {}

	def increase_last_order_idx(self, side: str) -> int:
		'''
		This function both increases the last order idx count and returns the idx, so that it can be used immediately.
		'''
		self.last_order_idx[side] += 1
		return self.last_order_idx[side]


	def add_limit_order(self, exchange_name: str, side: int, limit_price: int, trader_idx: int, timestamp: float) -> None:
		''''
		The function updates the number of last order on the market as a whole. This ensures uniqueness of the id per
		side on all exchanges. It then assigns the order and exchange to the Trader class for future reference.
		Finally it submits the order onto the appropriate exchange.
		'''
		order_idx = self.increase_last_order_idx(modules.misc.side_to_string(side))
		new_order = modules.misc.LimitOrder(
			idx = order_idx,
			side = modules.misc.side_to_orderbook_type(side),
			exchange_name = exchange_name
		)
		self.meta[new_order] = modules.misc.TraderTimestamp(
			trader_idx = trader_idx,
			timestamp = timestamp,
		)
		self.exchanges[exchange_name].add_order(
			side = modules.misc.side_to_orderbook_type(side),
			order_id = order_idx,
			price = limit_price,
			quantity = 1,
			position = None,
			metadata = {
				'timestamp': timestamp
			}
		)
		return {
			new_order: self.meta[new_order]
		}


	def execute_order(self, exchange_name: str, limit_order: modules.misc.LimitOrder, active_hit: bool = False) -> int:
		'''
		We execute the passive order, the limit_order_active parameter is given only in continuous trading.
		'''
		if not active_hit:
			filled_order = self.exchanges[exchange_name].fill_order(
				order_id = limit_order.idx,
				filled_quantity = 1,
				side = limit_order.side
			)
			self.total_number_of_trades += 1
		trader = self.meta[limit_order]
		# Only save orders, which have been in the orderbook for more than the length of the batch auction,
		# as those are the orders which have been in the orderbook as passive quotations.
		self.execution_times.append(self.current_time - trader.timestamp)
		return {
			limit_order: modules.misc.TraderTimestamp(
				trader_idx = trader.trader_idx,
				timestamp = self.current_time
			)
		}




	def save_market_information(self) -> None:
		'''
		Each cycle we save the information which the markets produce, from these we later compute metrics which measure the market's performance.
		'''
		pass


	def calculate_sample_price_series(self) -> None:
		'''
		Calculates price series
		'''
		price_series = pd.Series(self.asset.asset_price_series)
		price_series_index = price_series.index.tolist()
		price_series.index = [
			int(np.floor(price_index / settings.SAMPLING_PRICE_SERIES) * settings.SAMPLING_PRICE_SERIES)
			for price_index in price_series_index
		]
		self.resampled_price_series = price_series


	def calculate_volatility(self) -> float:
		return np.mean(np.log(np.std(
			self.resampled_price_series.groupby(self.resampled_price_series.index).last()
		)))


	def calculate_mean_of_bid_ask_spread(self) -> float:
		pass


	def calculate_mean_of_bid_ask_spread(self) -> float:
		pass