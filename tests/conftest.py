from typing import Any, Dict
import decimal
import unittest.mock
import pytest
import orderbook

import modules.asset
import modules.marketmaker
import modules.regulator
import modules.settings as settings
import modules.zerointelligence


@pytest.fixture
def orderbook_with_normal_bid_and_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**normal_bid())
	basic_orderbook.add_order(**normal_ask())
	return basic_orderbook


@pytest.fixture
def orderbook_with_best_bid_and_worst_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**best_bid())
	basic_orderbook.add_order(**worst_ask())
	return basic_orderbook


@pytest.fixture
def orderbook_with_worst_bid_and_best_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**worst_bid())
	basic_orderbook.add_order(**best_ask())
	return basic_orderbook


@pytest.fixture
def orderbook_with_normal_bid_and_no_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**normal_bid())
	return basic_orderbook


@pytest.fixture
def orderbook_with_no_bid_and_normal_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**normal_ask())
	return basic_orderbook


@pytest.fixture
def orderbook_with_best_bid_and_no_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**best_bid())
	return basic_orderbook


@pytest.fixture
def orderbook_with_no_bid_and_best_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**best_ask())
	return basic_orderbook


@pytest.fixture
def empty_orderbook():
	return orderbook.orderbook.NonUniqueIdOrderBook()
	

@pytest.fixture(scope = 'module')
def basic_asset() -> modules.asset.Asset:
	return modules.asset.Asset(
		initial_value = settings.INITIAL_ASSET_VALUE,
		mean_reversion_factor = settings.MEAN_REVERSION_FACTOR,
		sigma = settings.SIGMA_ASSET
	)


@pytest.fixture
def basic_regulator(basic_asset):
	return modules.regulator.Regulator(
		national_best_bid_and_offer_delay = settings.NATIONAL_BEST_BID_AND_OFFER_DELAY,
		asset = basic_asset,
	)


@pytest.fixture
def basic_zerointelligence(basic_regulator, empty_orderbook):
	return modules.zerointelligence.ZeroIntelligence(
		idx = 1,
		quantity_max = settings.QUANTITY_MAX,
		shading_min = settings.SHADING_MIN,
		shading_max = settings.SHADING_MAX,
		regulator = basic_regulator,
		default_exchange = settings.NAMES_OF_EXCHANGES[0],
	)


@pytest.fixture
def basic_marketmaker(basic_regulator, empty_orderbook):
	return modules.marketmaker.MarketMaker(
		idx = 1,
		regulator = basic_regulator,
		exchange_name = settings.NAMES_OF_EXCHANGES[0],
		number_of_orders = settings.MARKET_MAKER_NUMBER_ORDERS,
		ticks_between_orders = settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS,
		spread_around_asset = settings.MARKET_MAKER_SPREAD_AROUND_ASSET,
	)


@pytest.fixture(scope = 'session')
def best_bid() -> Dict[Any, Any]:
	return {
		'side': orderbook.OrderSide.BID,
		'price': 1000,
		'quantity': 1,
		'metadata': {
			'seconds': 1,
			'nanoseconds': 1
		},
		'order_id': 1,
		'position': None
	}


@pytest.fixture(scope = 'session')
def normal_bid() -> Dict[Any, Any]:
	return {
		'side': orderbook.OrderSide.BID,
		'price': 500,
		'quantity': 1,
		'metadata':{
			'seconds':1,
			'nanoseconds':1,
		},
		'order_id': 2,
		'position': None
	}


@pytest.fixture(scope = 'session')
def worst_bid() -> Dict[Any, Any]:
	return {
		'side': orderbook.OrderSide.BID,
		'price': 100,
		'quantity': 1,
		'metadata':{
			'seconds':1,
			'nanoseconds':1,
		},
		'order_id': 3,
		'position': None
	}


@pytest.fixture(scope = 'session')
def best_ask() -> Dict[Any, Any]:
	return {
		'side': orderbook.OrderSide.ASK,
		'price': 500,
		'quantity': 1,
		'metadata':{
			'seconds':1,
			'nanoseconds':1,
		},
		'order_id': 4,
		'position': None
	}


@pytest.fixture(scope = 'session')
def normal_ask() -> Dict[Any, Any]:
	return {
		'side': orderbook.OrderSide.ASK,
		'price': 1000,
		'quantity': 1,
		'metadata':{
			'seconds':1,
			'nanoseconds':1,
		},
		'order_id': 5,
		'position': None
	}


@pytest.fixture(scope = 'session')
def worst_ask() -> Dict[Any, Any]:
	return {
		'side': orderbook.OrderSide.ASK,
		'price': 5000,
		'quantity': 1,
		'metadata':{
			'seconds':1,
			'nanoseconds':1,
		},
		'order_id': 6,
		'position': None
	}