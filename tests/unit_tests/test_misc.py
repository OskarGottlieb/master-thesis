import modules.misc
import orderbook



def test_side_to_orderbook_type_output() -> None:
	side_buyer = modules.misc.side_to_orderbook_type(1)
	side_seller = modules.misc.side_to_orderbook_type(0)
	assert type(side_buyer) is orderbook.OrderSide
	assert type(side_seller) is orderbook.OrderSide


def test_side_to_string() -> None:
	side_buyer = modules.misc.side_to_string(1)
	side_seller = modules.misc.side_to_string(0)
	assert type(side_buyer) is str
	assert type(side_seller) is str
	assert side_buyer == 'bid'
	assert side_seller == 'ask'

