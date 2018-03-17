from typing import NamedTuple, Union
import random
import orderbook



class Order(NamedTuple):
	'''
	Similar to limit orderbook, but it is simply the order the trader submits, it does not have an ID and it does not sit
	in the orderbook.
	'''
	side: int
	limit_price:int
	exchange_name: str



class LimitOrder(NamedTuple):
	'''
	Contains information about the current limit order the trader has on an exchange.
	The order is then defined by its idx and by the side. The idx is unit per market (inter-exchange).
	The side is 1 (0) if the trader is has a long (short) limit order. The order does not contain price, as it can be moved
	in the orderbook on market clearing.
	'''
	idx: int
	side: orderbook.types.OrderSide
	exchange_name: str



class ExchangeInfo(NamedTuple):
	'''
	When we iterate over the exchanges, we want to save their best bid and ask prices along with the reference to the exchange.
	'''
	best_bid: int
	best_ask: int
	exchange: str



class ExchangeResponse(NamedTuple):
	'''
	Standardized response that the trader receives after he submits his instructions to the exchange.
	'''
	action: str
	price: int



class NBBO(NamedTuple):
	'''
	NBBO (abbreviation of National Best Bid and Offer) stores information about the best bid and ask values
	along with the respective exchanges at which the best bid and ask orders rest.
	'''
	bid: int
	ask: int
	bid_exchange: str
	ask_exchange: str



class TraderOrderIdx(NamedTuple):
	'''
	TraderOrderIdx is used for keeping track of both the order which has been submitted and trade who submitted it.
	'''
	trader_idx: int
	timestamp: float
	order: Union[Order,LimitOrder]



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

