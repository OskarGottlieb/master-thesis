from typing import Dict, List, NamedTuple
import collections
import copy
import orderbook

#import modules.arbitrageur
import modules.asset
import modules.misc
import modules.settings as settings



class ExchangeResponse(NamedTuple):
	'''
	Standardized response that the trader receives after he submits his instructions to the exchange.
	'''
	action: str
	price: int



class HistoricExchanges(NamedTuple):
	'''
	Slow traders see different NBBO than fast arbitrageur, we therefore keep the historic snapshot of the exchanges in
	order to show them the 'correct' NBBO based on the NBBO delay.
	'''
	exchanges: Dict[str, orderbook.orderbook.NonUniqueIdOrderBook]
	timestamp: float



class Regulator:
	def __init__(self, national_best_bid_and_offer_delay: float, asset: modules.asset.Asset) -> None:
		self.national_best_bid_and_offer_delay = national_best_bid_and_offer_delay
		self.accurate_national_best_bid_and_offer: modules.misc.NBBO = modules.misc.NBBO(None, None, None, None)
		self.asset = asset
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
		self.meta: Dict[modules.misc.CurrentOrder, Dict[str, Any]] = {}
		self.add_current_exchanges_to_historic_exchanges()


	def process_order(self, side: int, order_price: int, exchange_name: str) -> ExchangeResponse:
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
		else:
			self.last_order_idx[modules.misc.side_to_string(side)] += 1
		return ExchangeResponse(action, order_price)


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


	def convert_order_to_dictionary(self, order):
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
		'''
		for idx, historic_exchange in enumerate(self.historic_exchanges_list):
			if self.current_time - self.national_best_bid_and_offer_delay >= historic_exchange.timestamp:
				self.historic_exchanges_list = self.historic_exchanges_list[:max(idx, 1)]
				return
