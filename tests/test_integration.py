import mock
import orderbook

import modules.misc
import modules.regulator
import modules.settings as settings


def test_regulator_process_long_order_where_nbbo_ask_is_traders_order(basic_regulator,
	empty_orderbook, orderbook_with_best_bid_and_ask, basic_zerointelligence):
	'''
	If the NBBO is formed out of current trader's limit order, we need to check that he will ignore this order and trade
	as if the order were not there.
	'''
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: empty_orderbook,
		settings.NAMES_OF_EXCHANGES[1]: orderbook_with_best_bid_and_ask
	}
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	regulator_response = basic_regulator.process_order(
		side = 0,
		order_price = 1000,
		timestamp = 11,
		default_exchange = list(basic_regulator.exchanges.keys())[0],
		current_orders = [modules.misc.CurrentOrder(
			idx = 1,
			side = 1,
			price = 1000,
			exchange_name = settings.NAMES_OF_EXCHANGES[1]
		)]
	)

	assert regulator_response.exchange == list(basic_regulator.exchanges.keys())[0]
	assert regulator_response.action == 'A'
	assert regulator_response.price == 1000