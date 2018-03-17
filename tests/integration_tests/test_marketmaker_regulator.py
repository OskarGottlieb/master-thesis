from typing import Any, Dict
import mock
import orderbook
import pytest

import modules.settings as settings



@pytest.mark.parametrize('auction_length,new_york_orderbook,chicago_orderbook,estimate_of_asset_value,orders_count,\
ticks_between_orders,spread_around_asset,new_york_bid,new_york_ask,chicago_bid,chicago_ask', [
	(0, pytest.lazy_fixture('empty_orderbook'), pytest.lazy_fixture('orderbook_with_normal_bid_and_ask'), 500, 2, 5, 100, [450, 445], [550, 555], [500], [1000]),
])
@mock.patch('modules.marketmaker.MarketMaker.get_estimate_of_the_fundamental_value_of_the_asset')
def test_sending_orders_to_the_exchange(mock_estimate_of_asset, basic_marketmaker, basic_regulator, new_york_orderbook,
chicago_orderbook, estimate_of_asset_value, orders_count, ticks_between_orders, spread_around_asset, new_york_bid,
new_york_ask, chicago_bid, chicago_ask) -> None:
	'''
	We are testing that the function trims correctly the order ladders that it generates in self.generate_order_ladders(),
	that is it removes orders which would be executed immediately.
	'''
	mock_estimate_of_asset.return_value = estimate_of_asset_value
	settings.MARKET_MAKER_NUMBER_ORDERS = orders_count
	settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS = ticks_between_orders
	settings.MARKET_MAKER_SPREAD_AROUND_ASSET = spread_around_asset
	basic_regulator.exchanges = {
		settings.NAMES_OF_EXCHANGES[0]: new_york_orderbook,
		settings.NAMES_OF_EXCHANGES[1]: chicago_orderbook
	}
	basic_regulator.current_time = 1
	basic_regulator.add_current_exchanges_to_historic_exchanges()
	basic_regulator.remove_redundant_historic_exchanges()
	basic_marketmaker.do()

	resulting_prices = {}
	for exchange_name, exchange in basic_regulator.exchanges.items():
		for side in (orderbook.types.OrderSide.ASK, orderbook.types.OrderSide.BID):
			prices = list(exchange.get_side(side).get_prices())
			resulting_prices[(exchange_name, side)] = prices

	assert resulting_prices[(settings.NAMES_OF_EXCHANGES[0], orderbook.types.OrderSide.BID)] == new_york_bid
	assert resulting_prices[(settings.NAMES_OF_EXCHANGES[0], orderbook.types.OrderSide.ASK)] == new_york_ask
	assert resulting_prices[(settings.NAMES_OF_EXCHANGES[1], orderbook.types.OrderSide.BID)] == chicago_bid
	assert resulting_prices[(settings.NAMES_OF_EXCHANGES[1], orderbook.types.OrderSide.ASK)] == chicago_ask