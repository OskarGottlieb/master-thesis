from typing import Any, Dict, List, Optional, Tuple
import decimal
import math
import operator
import orderbook
import sys

import modules.misc
import modules.regulator
import modules.settings as settings


class Trader:
	'''
	The trader class has functions that every trader type will make use of - mainly sending orders onto the exchange.
	'''
	idx = 0
	
	def __init__(self, regulator: modules.regulator.Regulator) -> None:
		self.regulator = regulator
		self._last_order: Dict[str, Any] = None
		self.current_orders: [modules.misc.LimitOrder] = []
		self.trades: List[modules.misc.LimitOrder] = []
		self.last_entry = 0
		self.position = 0
		self.side: int = None
		self._idx = Trader.idx
		Trader.idx += 1


	def __str__(self):
		return(f'{self.__class__.__name__} {self._idx}')


	def __lt__(self, other):
		return self._idx < other._idx


	
	def execute_order(self, exchange_name: str) -> int:
		''''
		We first delete any existing limit orders. Then we proceed to the execution of a "market" type order.
		'''
		# mot side transforms True into False and vice versa
		side = modules.misc.side_to_orderbook_type(not self.side)
		best_order = self.regulator.exchanges[exchange_name].get_side(side).get_best()
		self.regulator.exchanges[exchange_name].fill_order(
			order_id = best_order.id,
			filled_quantity = 1,
			side = side
		)
		# We have to keep track of the trader who initially submitted the order onto the exchange.
		passive_side_order = modules.misc.LimitOrder(best_order.id, int(not self.side), best_order.price, exchange_name)
		trader_with_passive_limit_order = self.regulator.meta[
			passive_side_order
		]
		self.regulator.execution_times.append(self.regulator.current_time - trader_with_passive_limit_order['time_entry'])
		self.update_position_and_trades(
			order = modules.misc.LimitOrder(best_order.id, self.side, best_order.price, exchange_name)
		)
		return [modules.misc.TraderOrderIdx(
			trader_idx = trader_with_passive_limit_order['trader_idx'],
			order = passive_side_order
		)]


	def delete_order_from_an_exchange(self, order: modules.misc.LimitOrder, exchange_name: str,
	exchanges: Dict[str, orderbook.orderbook.NonUniqueIdOrderBook]) -> None:
		'''
		Given any exchange (be it historical, or real time), this function deletes an existing (!) limit order.
		'''
		exchanges[exchange_name].delete_order(
			order_id = order.idx,
			side = modules.misc.side_to_orderbook_type(order.side)
		)


	def update_position_and_trades(self, order: modules.misc.LimitOrder) -> None:
		'''
		Is called only in case of active/passive execution of an order.
		We add (subtract) 1 from the :param position: in case the trader's' buy (sell) order goes through.
		Also we add the current order to the list of trades.
		'''
		# If the execution is passive
		self.position += order.side if order.side else -1
		self.trades.append(order)
		self.add_private_utility_to_list()


	def add_private_utility_to_list(self, active_trade: bool = False) -> None:
		'''
		ZeroIntelligence traders have a private utility, the sum of these private utilities form the basis of ZI's surplus.
		'''
		if self.__class__.__name__ != 'ZeroIntelligence':
			return
		utility_sign = 1 if self.side else -1
		self.list_private_utility.append(utility_sign * self.private_utility)


	def get_estimate_of_the_fundamental_value_of_the_asset(self) -> decimal.Decimal:
		'''
		Represents equation (1), slightly rewritten.
		'''
		mean_value = self.regulator.asset.mean_value
		return mean_value + (self.regulator.asset.last_value - mean_value) * \
		(1 - settings.MEAN_REVERSION_FACTOR) ** (settings.SESSION_LENGTH - self.regulator.current_time)


	def get_national_best_bid_and_offer(self) -> str:
		'''
		Returns the latest orderbook snapshot, which is stored in the Regulator's historic_exchanges_list.
		'''
		return self.get_accurate_national_best_bid_and_offer(
			exchanges = self.regulator.historic_exchanges_list[-1].exchanges,
			current_orders = self.current_orders,
		)


	def get_accurate_national_best_bid_and_offer(self, current_orders: modules.misc.LimitOrder,
	exchanges: Dict[str, orderbook.orderbook.NonUniqueIdOrderBook]) -> modules.misc.NBBO:
		'''
		Gets the best bid and best ask values given a standard dict of exchanges.
		Works with both current (true) dict of exchanges as well as historic (lagged) dict of exchanges.
		If we are supplied with trader's current_orders, we first clean the orderbook, by removing his orders only then
		we take the orderbook snapshot.
		'''
		list_exchange_info: List[NamedTuple] = []
		if self.current_orders and self.last_entry + self.regulator.national_best_bid_and_offer_delay <= self.regulator.current_time:
			for order in self.current_orders:
				self.delete_order_from_an_exchange(
					order = order,
					exchange_name = order.exchange_name,
					exchanges = exchanges
				)
		for exchange_name, exchange in exchanges.items():
			best_bid, best_ask = [side.get_best().price if side else None for side in (exchange.bid, exchange.ask)]
			list_exchange_info.append(modules.misc.ExchangeInfo(
				best_bid = best_bid, 
				best_ask = best_ask,
				exchange = exchange_name,
			))
		bid_tuple = sorted([x for x in list_exchange_info if x.best_bid], key = operator.attrgetter('best_bid'), reverse = True)
		ask_tuple = sorted([x for x in list_exchange_info if x.best_ask], key = operator.attrgetter('best_ask'))
		bid, bid_exchange = (bid_tuple[0].best_bid, bid_tuple[0].exchange) if bid_tuple else (None, None)
		ask, ask_exchange = (ask_tuple[0].best_ask, ask_tuple[0].exchange) if ask_tuple else (None, None)
		return modules.misc.NBBO(
			bid = bid,
			ask = ask,
			bid_exchange = bid_exchange,
			ask_exchange = ask_exchange
		)


	def send_order_to_the_exchange(self, side: str, exchange_name: str, limit_price: int) -> List:
		'''
		We get back the info from the exchange (wrapped in the ExchangeResponse object), saying whether our order was executed or added to the orderbook.
		'''
		self.regulator.list_orders_to_be_processed.append(
			modules.misc.TraderOrderIdx(
				trader_idx = self._idx,
				timestamp = self.regulator.current_time,
				order = modules.misc.Order(
					side = side,
					limit_price = limit_price,
					exchange_name = exchange_name,
				)
			)
		)


	def process_exchange_response(self, side: str, exchange_name: str, action: str, price: int) -> Optional[Tuple[dict, modules.misc.LimitOrder]]:
		'''
		The information about the trader's intention (buying/selling at which price) is sent to the regulator and processed.
		Regulator knows of the (delayed) NBBO and therefore returns the exchange, action (adding a limit order or executing a
		resting order). If the trade is executed, the function returns the ID of the trader whose order has been executed.
		'''
		if action == 'A':
			nanoseconds, seconds = math.modf(self.regulator.current_time)
			self.add_limit_order(
				price = price, 
				seconds = seconds,
				nanoseconds = nanoseconds,
				exchange_name = exchange_name
			)
		else:
			return self.execute_order(
				exchange_name = exchange_name
			)
		return []


	def calculate_profit_from_trading(self):
		'''
		This function returns sum of short minus long trades - the position can be non-zero!
		'''
		long_trades = sum([trade.price for trade in self.trades if trade.side])
		short_trades = sum([trade.price for trade in self.trades if not trade.side])
		return short_trades - long_trades


	def calculate_value_of_final_position(self):
		'''
		Returns the remaining position (long, or short) multiplied by the last price of the asset.
		'''
		return self.position * self.regulator.asset.last_value