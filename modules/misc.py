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
	exchange: orderbook.orderbook.NonUniqueIdOrderBook



def side_to_orderbook_type(side: int):
	'''
	Converts the integer of 1 (0) into an appropriate side type.
	The OrderSide is then used when looking up values in the orderbook.
	'''
	if side not in (0, 1):
		raise ValueError(f'{side} is not a valid side input.')
	return orderbook.OrderSide.BID if side else orderbook.OrderSide.ASK


def side_to_string(side: int) -> str:
	if side not in (0, 1):
		raise ValueError(f'{side} is not a valid side input.')
	return 'bid' if side else 'ask'