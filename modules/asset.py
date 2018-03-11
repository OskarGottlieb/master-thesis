from typing import List
import decimal

import numpy as np



class Asset(object):
	'''
	The asset value is an exogenous variable, which can be pre-generated before the trading takes place.
	'''
	def __init__(self, initial_value: decimal.Decimal, mean_reversion_factor: float, sigma):
		self.value_series: List[int] = [initial_value]
		self.mean_reversion_factor: float = mean_reversion_factor
		self.sigma: float = sigma
		self.mean_value: float = None
		self.last_value: int = self.value_series[-1]


	def get_new_value(self):
		'''
		We first calculate the value of the mean reversion value process of the asset.
		For simplicity sake, apart from saving the value_series information, we also calculate the mean and
		last_value of the value series.
		'''
		current_value = max(int(self.last_value * self.mean_reversion_factor \
						+ np.mean(self.value_series) * (1 - self.mean_reversion_factor) \
						+ np.random.normal(0, self.sigma, 1)), 0)
		self.value_series.append(int(current_value))
		self.mean_value = np.mean(self.value_series)
		self.last_value = self.value_series[-1]