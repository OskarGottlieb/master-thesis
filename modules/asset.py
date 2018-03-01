from typing import List
import decimal

import numpy as np



class Asset(object):
	'''
	The asset price is an exogenous variable, which can be pre-generated before the trading takes place.
	'''
	def __init__(self, initial_price: decimal.Decimal, mean_reversion_factor: float, sigma):
		self.price_series: List[int] = [initial_price]
		self.mean_reversion_factor: float = mean_reversion_factor
		self.sigma: float = sigma
		self.mean_price: float = None
		self.last_price: int = self.price_series[-1]


	def get_new_price(self):
		'''
		We first calculate the value of the mean reversion price process of the asset.
		For simplicity sake, apart from saving the price_series information, we also calculate the mean and
		last_price of the price series.
		'''
		current_price = max(int(self.last_price * self.mean_reversion_factor \
						+ np.mean(self.price_series) * (1 - self.mean_reversion_factor) \
						+ np.random.normal(0, self.sigma, 1)), 0)
		self.price_series.append(int(current_price))
		self.mean_price = np.mean(self.price_series)
		self.last_price = self.price_series[-1]