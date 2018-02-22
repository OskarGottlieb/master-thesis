from typing import Any, Dict, List

import orderbook

import modules.misc
import modules.regulator



class Trader:
	'''
	The trader class has functions that every trader type will make use of - mainly sending orders onto the exchange.
	'''

	def __init__(self, regulator: modules.regulator.Regulator) -> None:
		self.regulator = regulator
		self._last_order: Dict[str, Any] = None
		self.current_order: modules.misc.CurrentOrder = None
		self.trades: List[modules.misc.CurrentOrder] = []


	def add_limit_order(self, price: int, seconds: int, nanoseconds: int,
	exchange: orderbook.orderbook.NonUniqueIdOrderBook) -> None:
		''''
		We first check whether the trader has any order on any exchange. If he has, we delete the order.
		Then the function updates the number of last order on the market as a whole. This should ensure uniqueness of
		the id per side on all exchanges.
		It then assigns the order and exchange to the Trader class for future reference.
		Finally it submits the order onto the appropriate exchange.
		'''
		order_idx = self.regulator.last_order_idx[modules.misc.side_to_string(self.side)]
		side = modules.misc.side_to_orderbook_type(self.side)
		self.current_order = modules.misc.CurrentOrder(order_idx, self.side, price, exchange)
		# We also want to share the information about the current trade with the regulator.
		# This way once the trader executes the trade, we know which trader to notify that his limit order has been filled.
		self.regulator.orders[self.current_order] = self._idx
		exchange.add_order(
			side = side,
			order_id = order_idx,
			price = price,
			quantity = 1,
			position = None,
			metadata = {
				'timestamp': seconds * int(1e9) + nanoseconds
			}
		)


	def execute_order(self, exchange: orderbook.orderbook.NonUniqueIdOrderBook) -> int:
		''''
		We first delete any existing limit orders. Then we proceed to the execution of a "market" type order.
		'''
		# mot side transforms True into False and vice versa
		side = modules.misc.side_to_orderbook_type(not self.side)
		best_order = exchange.get_side(side).get_best()
		exchange.fill_order(
			order_id = best_order.id,
			filled_quantity = 1,
			side = side
		)
		# We have to keep track of the trader who initially submitted the order onto the exchange.
		trader_id = self.regulator.orders[
			modules.misc.CurrentOrder(best_order.id, not self.side, best_order.price, exchange)
		]
		self.update_position_and_trades(current_order = modules.misc.CurrentOrder(best_order.id, self.side, best_order.price, exchange))
		return trader_id


	def delete_order(self) -> None:
		if self.current_order:
			self.current_order.exchange.delete_order(
				order_id = self.current_order.idx,
				side = modules.misc.side_to_orderbook_type(self.current_order.side)
			)
		self.current_order = None


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
