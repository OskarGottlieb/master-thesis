import mock
import numpy as np

import modules.asset
import modules.settings as settings


def test_asset_last_price(basic_asset) -> None:
    '''Tests that after init() the latest price equals that of the mean (there is only one)'''
    assert basic_asset.latest_price == np.mean(basic_asset.price_series)


@mock.patch('numpy.random.normal')
def test_asset_new_price(mock_random_normal, basic_asset) -> None:
    '''
    Tests that a new positive (negative) price shock is reflected in the Asset's attributes.
    '''
    mock_random_normal.return_value = 10
    basic_asset.get_new_price()
    assert basic_asset.latest_price == settings.INITIAL_ASSET_PRICE + 10
    assert basic_asset.mean_price == (2 * settings.INITIAL_ASSET_PRICE + 10) / 2
    
    mock_random_normal.return_value = -20
    basic_asset.get_new_price()
    assert basic_asset.latest_price == 9985
    assert basic_asset.mean_price == (2 * settings.INITIAL_ASSET_PRICE + 10 + 9985) / 3