from typing import Any, Dict
import mock
import orderbook
import pytest

import modules.settings as settings


@pytest.mark.parametrize('estimate_of_asset_price,spread_around_asset,expected_highest_bid,expected_lowest_ask', [
	(100, 20, 90, 110),
	(0, 10, 0, 5),
	(50, 100, 0, 100),
])
@mock.patch('modules.marketmaker.MarketMaker.get_estimate_of_the_fundamental_value_of_the_asset')
def test_generation_of_central_ladder_prices(mock_estimate_of_asset, estimate_of_asset_price,
spread_around_asset, expected_highest_bid, expected_lowest_ask, basic_marketmaker):
	mock_estimate_of_asset.return_value = estimate_of_asset_price
	settings.MARKET_MAKER_SPREAD_AROUND_ASSET = spread_around_asset
	highest_bid, lowest_ask = basic_marketmaker.get_central_ladder_prices()
	assert highest_bid == expected_highest_bid
	assert lowest_ask == expected_lowest_ask


@pytest.mark.parametrize('highest_bid,lowest_ask,number_of_orders,number_of_ticks_between_orders,\
expected_ladder_bids,expected_ladder_asks', [
	(50, 100, 2, 5, [50, 45], [100, 105]),
	(0, 5, 3, 10, [], [5, 15, 25]),
	(30, 40, 3, 15, [30, 15], [40, 55, 70]),
])
def test_generation_ladder_of_orders(highest_bid, lowest_ask, number_of_orders,
number_of_ticks_between_orders, expected_ladder_bids, expected_ladder_asks, basic_marketmaker):
	settings.MARKET_MAKER_NUMBER_ORDERS = number_of_orders
	settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS = number_of_ticks_between_orders
	ladder_bids, ladder_asks = basic_marketmaker.generate_order_ladders(
		highest_bid = highest_bid,
		lowest_ask = lowest_ask
	)
	assert ladder_bids == expected_ladder_bids
	assert ladder_asks == expected_ladder_asks


@pytest.mark.parametrize('new_york_orderbook,chicago_orderbook,ladder_bids,ladder_asks,\
expected_trimmed_ladder_bids,expected_trimmed_ladder_asks,set_global_delay', [
	(pytest.lazy_fixture('empty_orderbook'), pytest.lazy_fixture('orderbook_with_best_bid_and_no_ask'), [100, 200, 300], [400, 500, 1500], [100, 200, 300], [1500], 0),
	(pytest.lazy_fixture('empty_orderbook'), pytest.lazy_fixture('orderbook_with_no_bid_and_best_ask'), [500, 1000, 1500], [400, 500, 1500], [], [400, 500, 1500], 0),
	(pytest.lazy_fixture('empty_orderbook'), pytest.lazy_fixture('empty_orderbook'), [100, 200, 400], [500, 1000, 1500], [100, 200, 400], [500, 1000, 1500], 0),
	(pytest.lazy_fixture('orderbook_with_normal_bid_and_no_ask'), pytest.lazy_fixture('orderbook_with_no_bid_and_normal_ask'), [], [], [], [], 0),
])
def test_trim_orders_ladder(basic_marketmaker, basic_regulator, new_york_orderbook, chicago_orderbook, ladder_bids, ladder_asks,
expected_trimmed_ladder_bids, expected_trimmed_ladder_asks, set_global_delay) -> None:
	'''
	We are testing that the function trims correctly the order ladders that it generates in self.generate_order_ladders(),
	that is it removes orders which would be executed immediately.
	'''
	settings.NATIONAL_BEST_BID_AND_OFFER_DELAY = set_global_delay
	basic_marketmaker.exchange_name = settings.NAMES_OF_EXCHANGES[1]
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: new_york_orderbook,
		settings.NAMES_OF_EXCHANGES[1]: chicago_orderbook
	}
	basic_regulator.current_time = 1
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	basic_regulator.remove_redundant_historic_exchanges()
	trimmed_ladder_bids, trimmed_ladder_asks = basic_marketmaker.trim_orders_ladder(
		ladder_bids = ladder_bids,
		ladder_asks = ladder_asks,
	)

	assert trimmed_ladder_bids == expected_trimmed_ladder_bids
	assert trimmed_ladder_asks == expected_trimmed_ladder_asks
