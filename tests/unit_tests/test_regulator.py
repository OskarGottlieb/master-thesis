import mock
import orderbook
import pytest

import modules.regulator
import modules.settings as settings




def test_copying_exchange(basic_regulator, orderbook_with_normal_bid_and_ask, empty_orderbook):
	'''
	Testing of copying both an orderbook with and without orders.
	'''
	old_exchange = orderbook_with_normal_bid_and_ask
	old_exchange_empty = empty_orderbook
	new_exchange = basic_regulator.copy_all_orders_from_one_exchange_to_another(old_exchange)
	new_exchange_empty = basic_regulator.copy_all_orders_from_one_exchange_to_another(old_exchange_empty)
	for exchange_side in zip(old_exchange.bid, new_exchange.bid), zip(old_exchange.ask, new_exchange.ask):
		for order_old_exchange, order_new_exchange in exchange_side:
			assert order_old_exchange == order_new_exchange
	assert list(new_exchange_empty.bid) == list(new_exchange_empty.ask) == []


def test_converting_order_into_dictionary(basic_regulator):
	order = orderbook.types.Order(
		id = 1,
		price = 500,
		quantity = 1,
		side = orderbook.OrderSide.BID,
		metadata = {
			'seconds': 1,
			'nanoseconds': 1
		}
	)
	order_dictionary = basic_regulator.convert_order_to_dictionary(order)
	expected_dictionary = {
		'side': orderbook.OrderSide.BID,
		'order_id': 1,
		'price': 500,
		'quantity': 1,
		'position': None,
		'metadata': {
			'seconds': 1,
			'nanoseconds': 1
		}
	}
	assert order_dictionary == expected_dictionary


def test_getting_orders_to_be_cleared(basic_regulator, orderbook_with_higher_bid_than_ask, empty_orderbook):
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook_with_higher_bid_than_ask,
		settings.NAMES_OF_EXCHANGES[1]: empty_orderbook
	}