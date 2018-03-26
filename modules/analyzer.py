from typing import Any, Dict
import itertools
import logwood
import multiprocessing
import os
import random
import pandas as pd

import modules.database
import modules.god
import modules.settings as settings



class Analyzer:
	'''
	Analyzer class calls methods which define sets of parameters which we test in the preliminary testing.
	'''

	def __init__(self) -> None:
		self.list_parameters_sets: List[Dict[str: List[Any]]] = []
		self.base_dicitonary = settings.BASE_DICTIONARY
		self.final_dataframe = pd.DataFrame()
		self.generate_parameters_sets()
		self.fill_database_with_parameters_sets()


	@staticmethod
	def expand_grid(data_dictionary: Dict[Any, Any]):
		rows = itertools.product(*data_dictionary.values())
		return pd.DataFrame.from_records(rows, columns = data_dictionary.keys())


	def generate_parameters_sets(self) -> None:
		'''
		Calls all functions which call 
		'''
		self.zero_intelligence_atribute()
		self.market_makers_count()
		self.market_makers_attributes()
		self.different_session_length()
		self.arbitrageur_presence_no_arbitrage()
		self.lagged_nbbo_without_arbitrageur()
		self.batch_auction_without_lag()
		self.batch_auction_with_lag()
		self.lagged_nbbo_without_arbitrageur_continuous()
		self.arbitrageur_presence_no_arbitrage()



	def zero_intelligence_atribute(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['zero_intelligence_shading_max'] = list(range(0, 1000, 100))
		self.list_parameters_sets.append(self.expand_grid(dictionary))


	def market_makers_count(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['market_maker_count'] = [0, 2, 4]
		self.list_parameters_sets.append(self.expand_grid(dictionary))
	

	def market_makers_attributes(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['market_maker_intensity'] = [0.0005, 0.001, 0.005]
		dictionary['market_maker_number_of_ticks_between_orders'] = [50, 100, 200, 300]
		dictionary['market_maker_spread_around_asset'] = [0, 2, 4]
		dictionary['market_maker_number_orders'] = [2, 5, 10]
		self.list_parameters_sets.append(self.expand_grid(dictionary))
	

	def different_session_length(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['session_length'] = [int(1e3), int(5e3), int(10e3)]
		self.list_parameters_sets.append(self.expand_grid(dictionary))


	def arbitrageur_presence_no_arbitrage(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['include_arbitrageur'] = [True, False]
		self.list_parameters_sets.append(self.expand_grid(dictionary))


	def lagged_nbbo_without_arbitrageur(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['national_best_bid_and_offer_delay'] = list(range(0, 1000, 100))
		self.list_parameters_sets.append(self.expand_grid(dictionary))


	def batch_auction_without_lag(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['batch_auction_length'] = list(range(0, 1000, 100))
		self.list_parameters_sets.append(self.expand_grid(dictionary))


	def batch_auction_with_lag(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['national_best_bid_and_offer_delay'] = list(range(0, 1000, 100))
		dictionary['batch_auction_length'] = list(range(0, 1000, 100))
		dictionary['include_arbitrageur'] = [True, False]
		self.list_parameters_sets.append(self.expand_grid(dictionary))


	def lagged_nbbo_without_arbitrageur_continuous(self) -> None:
		dictionary = dict(self.base_dicitonary)
		dictionary['national_best_bid_and_offer_delay'] = list(range(0, 1000, 100))
		dictionary['batch_auction_length'] = list(range(0, 1000, 100))
		self.list_parameters_sets.append(self.expand_grid(dictionary))


	def fill_database_with_parameters_sets(self) -> None:
		for parameter_set in self.list_parameters_sets:
			self.final_dataframe = self.final_dataframe.append(parameter_set)
		modules.database.fill_parameters_table(self.final_dataframe)