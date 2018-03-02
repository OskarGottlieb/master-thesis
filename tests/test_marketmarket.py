from typing import Any, Dict
import mock
import orderbook
import pytest

import modules.settings as settings


@pytest.mark.parametrize('estimate_of_asset_price,spread_around_asset,highest_bid,lowest_ask', [
	(100, 20, 90, 110),
	(0, 10, 0, 5),
	(50, 100, 0, 100),
])
@mock.patch('modules.marketmaker.MarketMaker.get_estimate_of_the_fundamental_value_of_the_asset')
def test_generation_of_central_ladder_prices(mock_estimate_of_asset, estimate_of_asset_price,
spread_around_asset, highest_bid, lowest_ask, basic_marketmaker):
	mock_estimate_of_asset.return_value = estimate_of_asset_price
	settings.MARKET_MAKER_SPREAD_AROUND_ASSET = spread_around_asset
	highest_bid_estimate, lowest_ask_estimate = basic_marketmaker.get_central_ladder_prices()
	assert highest_bid_estimate == highest_bid
	assert lowest_ask_estimate == lowest_ask


@pytest.mark.parametrize('central_ladder_prices,number_of_orders,number_of_ticks_between_orders,list_bids,list_asks', [
    ((50, 100), 2, 5, [50, 45], [100, 105]),
    ((0, 5), 3, 10, [], [5, 15, 25]),
    ((30, 40), 3, 15, [30, 15], [40, 55, 70]),
])
@mock.patch('modules.marketmaker.MarketMaker.get_central_ladder_prices')
def test_generation_ladder_of_orders(mock_central_ladder_prices, central_ladder_prices,
number_of_orders, number_of_ticks_between_orders, list_bids, list_asks, basic_marketmaker):
	mock_central_ladder_prices.return_value = central_ladder_prices
	settings.MARKET_MAKER_NUMBER_ORDERS = number_of_orders
	settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS = number_of_ticks_between_orders
	list_bids_estimate, list_asks_estimate = basic_marketmaker.generate_order_ladders()
	assert list_bids_estimate == list_bids
	assert list_asks_estimate == list_asks
