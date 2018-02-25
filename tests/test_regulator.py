import mock
import orderbook

import modules.regulator
import modules.settings as settings



def test_regulator_process_long_order_with_two_empty_orderbooks(basic_regulator):
	'''
	There is no NBBO, no other orders, therefore the order should simply be added to the orderbook.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook.orderbook.NonUniqueIdOrderBook(),
		settings.NAMES_OF_EXCHANGES[1]: orderbook.orderbook.NonUniqueIdOrderBook()
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 1,
		order_price = 500,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'A'
	assert exchange_response.price == 500


def test_regulator_process_long_order_with_one_empty_orderbook_and_normal_ask(basic_regulator,
	orderbook_with_no_bid_and_normal_ask):
	'''
	There is already one order in the market, but our order's price is too low,
	therefore it still should only be added to the default orderbook.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook.orderbook.NonUniqueIdOrderBook(),
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_no_bid_and_normal_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 1,
		order_price = 500,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'A'
	assert exchange_response.price == 500


def test_regulator_process_long_order_with_one_empty_orderbook_and_best_ask(basic_regulator,
	orderbook_with_no_bid_and_best_ask):
	'''
	The best (therefore low) ask allows us to execute right away against the resting order.
	Although the trader would add order with price 1000, he wants to make use of the better price and therefore executes his order.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook.orderbook.NonUniqueIdOrderBook(),
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_no_bid_and_best_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 1,
		order_price = 1000,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'E'
	assert exchange_response.price == 500


def test_regulator_process_long_order_with_normal_and_best_ask(basic_regulator,
	orderbook_with_normal_bid_and_ask, orderbook_with_best_bid_and_ask):
	'''
	In this case, the trader should be able to execute at his own exchange, but given that the other exchange 
	offers better price, he will route his order and obtain a better execution price.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook_with_normal_bid_and_ask,
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_best_bid_and_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 1,
		order_price = 1000,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'E'
	assert exchange_response.price == 500
	

def test_regulator_process_long_order_with_two_bids_but_no_ask(basic_regulator,
	orderbook_with_normal_bid_and_no_ask, orderbook_with_best_bid_and_no_ask):
	'''
	Both exchanges have defined bid, but since we're buying, the buyer should simply add the order to his default orderbook.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook_with_normal_bid_and_no_ask,
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_best_bid_and_no_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 1,
		order_price = 1000,
		exchange_name = list(basic_regulator.exchanges.keys())[1],
	)
	
	assert exchange_response.action == 'A'
	assert exchange_response.price == 1000


def test_regulator_process_short_order_with_two_empty_orderbooks(basic_regulator):
	'''
	There is no NBBO, no other orders, therefore the order should simply be added to the orderbook.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook.orderbook.NonUniqueIdOrderBook(),
		settings.NAMES_OF_EXCHANGES[1]: orderbook.orderbook.NonUniqueIdOrderBook()
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 0,
		order_price = 1000,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'A'
	assert exchange_response.price == 1000


def test_regulator_process_short_order_with_one_empty_orderbook_and_normal_bid(basic_regulator,
	orderbook_with_normal_bid_and_no_ask):
	'''
	There is already one order in the market, but our order's price is too high,
	therefore it still should only be added to the default orderbook.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook.orderbook.NonUniqueIdOrderBook(),
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_normal_bid_and_no_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 0,
		order_price = 1000,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'A'
	assert exchange_response.price == 1000


def test_regulator_process_short_order_with_one_empty_orderbook_and_best_bid(basic_regulator,
	orderbook_with_best_bid_and_no_ask):
	'''
	The best (therefore high) bid allows us to execute right away against the resting order.
	Although the trader would add order with price 1000, he wants to make use of the better price and therefore executes his order.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook.orderbook.NonUniqueIdOrderBook(),
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_best_bid_and_no_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 0,
		order_price = 500,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'E'
	assert exchange_response.price == 1000


def test_regulator_process_short_order_with_normal_and_best_bid(basic_regulator,
	orderbook_with_normal_bid_and_ask, orderbook_with_best_bid_and_ask):
	'''
	In this case, the trader should be able to execute at his own exchange, but given that the other exchange 
	offers better price, he will route his order and obtain a better execution price.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook_with_normal_bid_and_ask,
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_best_bid_and_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 0,
		order_price = 500,
		exchange_name = list(basic_regulator.exchanges.keys())[0],
	)
	
	assert exchange_response.action == 'E'
	assert exchange_response.price == 1000
	

def test_regulator_process_short_order_with_two_asks_but_no_bid(basic_regulator,
	orderbook_with_no_bid_and_normal_ask, orderbook_with_no_bid_and_best_ask):
	'''
	Both exchanges have defined ask, but since we're selling, the seller should simply add the order to his default orderbook.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: orderbook_with_no_bid_and_normal_ask,
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_no_bid_and_best_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	exchange_response = basic_regulator.process_order(
		side = 0,
		order_price = 1000,
		exchange_name = list(basic_regulator.exchanges.keys())[1],
	)
	
	assert exchange_response.action == 'A'
	assert exchange_response.price == 1000


