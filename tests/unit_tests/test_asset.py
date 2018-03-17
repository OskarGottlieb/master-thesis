import mock
import numpy as np

import modules.asset
import modules.settings as settings


def test_asset_last_value(basic_asset) -> None:
    '''Tests that after init() the latest value equals that of the mean (there is only one)'''
    assert basic_asset.last_value == np.mean(basic_asset.value_series)


@mock.patch('numpy.random.normal')
def test_asset_new_value(mock_random_normal, basic_asset) -> None:
    '''
    Tests that a new positive (negative) value shock is reflected in the Asset's attributes.
    '''
    mock_random_normal.return_value = 10
    basic_asset.get_new_value()
    assert basic_asset.last_value == settings.INITIAL_ASSET_VALUE + 10
    assert basic_asset.mean_value == (2 * settings.INITIAL_ASSET_VALUE + 10) / 2
    
    mock_random_normal.return_value = -20
    basic_asset.get_new_value()
    assert basic_asset.last_value == 9985
    assert basic_asset.mean_value == (2 * settings.INITIAL_ASSET_VALUE + 10 + 9985) / 3