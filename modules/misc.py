from typing import NamedTuple
import orderbook



class CurrentOrder(NamedTuple):
	'''
	Contains information about the current limit order the trader has on an exchange.
	The order is then defined by its idx and by the side. The idx is unit per market (inter-exchange).
	The side is 1 (0) if the trader is has a long (short) limit order.
	Finally price is the prices at which the order sits in the orderbook.
	'''
	idx: int
	side: int
	price:int
	exchange_name: str



class ExchangeInfo(NamedTuple):
	'''
	When we iterate over the exchanges, we want to save their best bid and ask prices along with the reference to the exchange.
	'''
	best_bid: int
	best_ask: int
	exchange: str



class NBBO(NamedTuple):
	'''
	NBBO (abbreviation of National Best Bid and Offer) stores information about the best bid and ask values
	along with the respective exchanges at which the best bid and ask orders rest.
	'''
	bid: int
	ask: int
	bid_exchange: str
	ask_exchange: str



class TraderIdx(NamedTuple):
	'''
	TraderIdx uniquely identifies a trader among all traders.
	'''
	idx: int
	type: str



def side_to_orderbook_type(side: int):
	'''
	Converts the integer of 1 (0) into an appropriate side type.
	The OrderSide is then used when looking up values in the orderbook.
	'''
	assert side in (0, 1), f'{side} is not a valid side input.'
	return orderbook.OrderSide.BID if side else orderbook.OrderSide.ASK


def side_to_string(side: int) -> str:
	assert side in (0, 1), f'{side} is not a valid side input.'
	return 'bid' if side else 'ask'