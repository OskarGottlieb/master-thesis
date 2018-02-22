from typing import Dict, List, NamedTuple
import operator
import orderbook

#import modules.arbitrageur
import modules.asset
import modules.misc



class ExchangeInfo(NamedTuple):
	best_bid: int
	best_ask: int
	exchange: orderbook.orderbook.NonUniqueIdOrderBook



class NBBO(NamedTuple):
	bid: int
	ask: int
	bid_exchange: orderbook.orderbook.NonUniqueIdOrderBook
	ask_exchange: orderbook.orderbook.NonUniqueIdOrderBook
	timestamp: float



class RegulatorResponse(NamedTuple):
	exchange: orderbook.orderbook.NonUniqueIdOrderBook
	action: str
	price: int



class Regulator:
	def __init__(self, NBBO_delay: float, asset: modules.asset.Asset, list_exchanges: List[orderbook.orderbook.NonUniqueIdOrderBook]) -> None:
		self.NBBO_delay = NBBO_delay
		self.list_NBBO = [
			NBBO(None, None, None, None, 0)
		]
		self.NBBO: NBBO = self.list_NBBO[-1]
		self.asset = asset
		self._list_exchanges = list_exchanges
		self.current_time = 0
		self.last_order_idx: Dict[str, int] = {'bid': 0, 'ask': 0}
		# Orders will held information about the trader who is behind the order.
		# This way we know which trader to call to mark his trade as executed, once the trade is...executed.
		self.orders: Dict[modules.misc.CurrentOrder, int] = {}
		#self.arbitrageur = modules.arbitrageur.Arbitrageur(regulator = self)


	def process_order(self, side: int, order_price: int, timestamp: float,
	default_exchange: orderbook.orderbook.NonUniqueIdOrderBook) -> RegulatorResponse:
		'''
		The order comes in and we need to decide, whether it will be routed to the other exchange and if we will
		add it to the orderbook or execute it against a resting order. I picked doing it this way, as once the
		delay comes into play, the trader does not immediately know what will happen with his trade. After all, he 
		is looking at a lagged, non up-to-date information.
		'''
		self.get_latest_NBBO()
		side_type = modules.misc.side_to_orderbook_type(not side)
		exchange = default_exchange
		action = 'A'
		# The default exchange does not have to have orders on one side, that is when the OrderSideEmpty exceptions
		# is triggered and instead best_price is the best bid/ask.
		try:
			best_price = exchange.get_side(side_type).get_best().price
		except orderbook.exceptions.OrderSideEmpty:
			best_price = self.NBBO.ask if side else self.NBBO.bid
		if best_price:
			if side and self.NBBO.ask:
				if order_price >= self.NBBO.ask and self.NBBO.ask <= best_price:
					exchange = self.NBBO.ask_exchange
					order_price = best_price = self.NBBO.ask
					action = 'E'
			elif not side and self.NBBO.bid:
				if order_price <= self.NBBO.bid and self.NBBO.bid >= best_price:
					exchange = self.NBBO.bid_exchange
					order_price = best_price = self.NBBO.bid
					action = 'E'
		if action == 'A':
			self.last_order_idx[modules.misc.side_to_string(side)] += 1
		return RegulatorResponse(exchange, action, order_price)


	def save_current_NBBO(self, timestamp:float) -> None:
		'''
		Gets the best bid and best ask in the list of all the exchanges.
		It adds the value at the end of NBBO list, from which we then take the 'correctly lagged' NBBO value.
		'''
		exchanges: List[NamedTuple] = []
		for exchange in self._list_exchanges:
			best_bid, best_ask = [side.get_best().price if side else None for side in (exchange.bid, exchange.ask)]
			exchanges.append(ExchangeInfo(
				best_bid = best_bid, 
				best_ask = best_ask,
				exchange = exchange,
			))
		bid_tuple = sorted([x for x in exchanges if x.best_bid], key = operator.attrgetter('best_bid'), reverse = True)
		ask_tuple = sorted([x for x in exchanges if x.best_ask], key = operator.attrgetter('best_ask'))
		bid, bid_exchange = (bid_tuple[0].best_bid, bid_tuple[0].exchange) if bid_tuple else (None, None)
		ask, ask_exchange = (ask_tuple[0].best_ask, ask_tuple[0].exchange) if ask_tuple else (None, None)
		# We add the latest NBBO information as the 0th element of the self.list_NBBO list. This way we can iterate over
		# the list and on the first occurence of a timestamp which is at least lagged by the self.NBBO_delay constant we
		# can make the cut off.
		self.list_NBBO.insert(0, NBBO(
			bid = bid,
			ask = ask,
			bid_exchange = bid_exchange,
			ask_exchange = ask_exchange,
			timestamp = timestamp
		))


	def get_latest_NBBO(self) -> None:
		'''
		Given the NBBO delay, we iterate through the list of past NBBO values.
		While iterating, we want to achieve two things. Pick the correct value given the current timestamp and
		remove all redundant NBBOs from the list. Then we will set the NBBO displayed to non-Arbitrageur players
		as the last element of that list.
		'''
		latest_timestamp = self.list_NBBO[0].timestamp
		for idx, national_best_bid_and_offer in enumerate(self.list_NBBO):
			if latest_timestamp - self.NBBO_delay >= national_best_bid_and_offer.timestamp:
				self.list_NBBO[:] = self.list_NBBO[:max(idx, 1)]
				break
		self.NBBO = self.list_NBBO[-1]

