from typing import Any, Dict
import decimal
import unittest.mock
import pytest
import orderbook

import modules.asset
import modules.regulator
import modules.settings as settings



@pytest.fixture
def orderbook_with_normal_bid_and_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**normal_bid())
	basic_orderbook.add_order(**normal_ask())
	return basic_orderbook


@pytest.fixture
def orderbook_with_best_bid_and_ask():
	basic_orderbook = orderbook.orderbook.NonUniqueIdOrderBook()
	basic_orderbook.add_order(**best_bid())
	basic_orderbook.add_order(**best_ask())
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
		initial_price = settings.INITIAL_ASSET_PRICE,
		mean_reversion_factor = settings.MEAN_REVERSION_FACTOR,
		sigma = settings.SIGMA_ASSET
	)


@pytest.fixture
def basic_regulator(basic_asset):
	return modules.regulator.Regulator(
		NBBO_delay = settings.NBBO_DELAY,
		asset = basic_asset,
		list_exchanges = []
	)


@pytest.fixture
def basic_zerointelligence(basic_regulator, empty_orderbook):
	return modules.zerointelligence.ZeroIntelligence(
		idx = 1,
		quantity_max = settings.QUANTITY_MAX,
		shading_min = settings.SHADING_MIN,
		shading_max = settings.SHADING_MAX,
		regulator = basic_regulator,
		default_exchange = empty_orderbook,
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