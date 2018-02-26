from typing import Any, Dict, List
import operator
import orderbook

import modules.misc
import modules.regulator



class Trader:
	'''
	The trader class has functions that every trader type will make use of - mainly sending orders onto the exchange.
	'''

	def __init__(self, regulator: modules.regulator.Regulator, idx: int) -> None:
		self.regulator = regulator
		self._last_order: Dict[str, Any] = None
		self.current_order: modules.misc.CurrentOrder = None
		self.trades: List[modules.misc.CurrentOrder] = []
		self.last_entry = 0
		self.position = 0
		self.side: int = None
		self._idx = idx


	def __str__(self):
		return(f'{self.__class__.__name__} {self._idx}')


	def __lt__(self, other):
		return self._idx < other._idx


	def add_limit_order(self, price: int, seconds: int, nanoseconds: int, exchange_name:str) -> None:
		''''
		We first check whether the trader has any order on any exchange. If he has, we delete the order.
		Then the function updates the number of last order on the market as a whole. This should ensure uniqueness of
		the id per side on all exchanges.
		It then assigns the order and exchange to the Trader class for future reference.
		Finally it submits the order onto the appropriate exchange.
		'''
		order_idx = self.regulator.last_order_idx[modules.misc.side_to_string(self.side)]
		side = modules.misc.side_to_orderbook_type(self.side)
		self.current_order = modules.misc.CurrentOrder(order_idx, self.side, price, exchange_name)
		self.last_entry = seconds + nanoseconds
		# We also want to share the information about the current trade with the regulator.
		# This way once the trader executes the trade, we know which trader to notify that his limit order has been filled.
		self.regulator.orders[self.current_order] = self._idx
		self.regulator.exchanges[exchange_name].add_order(
			side = side,
			order_id = order_idx,
			price = price,
			quantity = 1,
			position = None,
			metadata = {
				'timestamp': seconds * int(1e9) + nanoseconds * int(1e18)
			}
		)


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
		trader_id = self.regulator.orders[
			modules.misc.CurrentOrder(best_order.id, not self.side, best_order.price, exchange_name)
		]
		self.update_position_and_trades(current_order = modules.misc.CurrentOrder(best_order.id, self.side, best_order.price, exchange_name))
		return trader_id


	def delete_order_from_an_exchange(self, exchange_name: str,
	exchanges: Dict[str, orderbook.orderbook.NonUniqueIdOrderBook]) -> None:
		exchanges[exchange_name].delete_order(
			order_id = self.current_order.idx,
			side = modules.misc.side_to_orderbook_type(self.current_order.side)
		)


	def update_position_and_trades(self, current_order: modules.misc.CurrentOrder = None) -> None:
		'''
		Is called only in case of active/passive execution of an order.
		We add (subtract) 1 from the :param position: in case the trader's' buy (sell) order goes through.
		Also we add the latest trade.
		'''
		# If the execution is passive
		side = self.current_order.side if self.current_order else self.side
		self.position += side if side else -1
		if current_order:
			self.trades.append(current_order)
		else:
			self.trades.append(self.current_order)


	def get_accurate_national_best_bid_and_offer(self, current_order: modules.misc.CurrentOrder,
	exchanges: Dict[str, orderbook.orderbook.NonUniqueIdOrderBook]) -> modules.misc.NBBO:
		'''
		Gets the best bid and best ask values given a standard dict of exchanges.
		Works with both current (true) dict of exchanges as well as historic (lagged) dict of exchanges.
		If we are supplied with trader's current_order, we first clean the orderbook, by removing his order only then
		we take the orderbook snapshot.
		'''
		list_exchange_info: List[NamedTuple] = []
		if self.current_order and self.last_entry + self.regulator.national_best_bid_and_offer_delay <= self.regulator.current_time:
			self.delete_order_from_an_exchange(exchange_name = self.current_order.exchange_name, exchanges = exchanges)
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