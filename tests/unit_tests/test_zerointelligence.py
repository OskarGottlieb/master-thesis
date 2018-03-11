from typing import Any, Dict
import mock
import orderbook
import pytest

import modules.zerointelligence


@mock.patch('numpy.random.normal')
def test_private_component_gain(mock_random_normal, basic_zerointelligence):
	mock_random_normal.return_value = [-3, 2, 3, 1, -1, 0, -2, 4]
	private_gain = basic_zerointelligence.generate_private_component_gain()
	assert private_gain == [4, 3, 2, 1, 0, -1, -2, -3]


@mock.patch.object(modules.zerointelligence.ZeroIntelligence, 'generate_private_component_gain')
def test_private_utility_of_the_asset(mock_private_component_gain, basic_zerointelligence):
	mock_private_component_gain.return_value = [4, 3, 2, 1, 0, -1, -2 , -3]
	basic_zerointelligence.side = 1
	basic_zerointelligence.position = 2
	basic_zerointelligence.quantity_max = 4
	private_utility_buyer = basic_zerointelligence.get_private_utility_of_the_asset()
	basic_zerointelligence.side = 0
	basic_zerointelligence.position = -2
	private_utility_seller = basic_zerointelligence.get_private_utility_of_the_asset()
	
	assert private_utility_buyer == -2 
	assert private_utility_seller == 3 
