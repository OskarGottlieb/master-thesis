from typing import List
import itertools
import random
import numpy as np
import pandas as pd
import orderbook

import modules.asset
import modules.settings as settings
import modules.regulator
import modules.zerointelligence
import modules.arbitrageur


class God:
	'''
	God knows everything and controls everything.
	'''
	def __init__(self) -> None:
		self._asset = modules.asset.Asset(settings.INITIAL_ASSET_PRICE, settings.MEAN_REVERSION_FACTOR, settings.SIGMA_ASSET)
		self._regulator: modules.regulator.Regulator = modules.regulator.Regulator(
			national_best_bid_and_offer_delay = settings.NATIONAL_BEST_BID_AND_OFFER_DELAY,
			asset = self._asset,
		)
		self._list_zero_intelligence_traders: List[modules.zerointelligence.ZeroIntelligence] = [
			modules.zerointelligence.ZeroIntelligence(
				idx = i,
				quantity_max = settings.QUANTITY_MAX,
				shading_min = settings.SHADING_MIN,
				shading_max = settings.SHADING_MAX,
				regulator = self._regulator,
				default_exchange = random.choice(list(self._regulator.exchanges.keys())),
			) for i in range(settings.ZERO_INTELLIGENCE_COUNT)
		]
		self._arbitrageur = modules.arbitrageur.Arbitrageur(regulator = self._regulator)
		self._summarized_entries: pd.Series = None
		self.summarize_entries()


	def summarize_entries(self) -> None:
		'''
		Creates a grouped series equal in length to the number of zerointelligence traders times the session length.
		Then randomly (with equal probability) assigns a value to the given trader.
		It cuts all traders above the original length of the session length.
		'''
		summarized_entries_times = np.random.exponential(1 / settings.INTENSITY, settings.SESSION_LENGTH * settings.ZERO_INTELLIGENCE_COUNT)
		grouped_entries_series = pd.Series(
			index = np.random.choice(self._list_zero_intelligence_traders, settings.SESSION_LENGTH * settings.ZERO_INTELLIGENCE_COUNT),
			data = summarized_entries_times
		).groupby(level = 0).cumsum()
		self._summarized_entries = pd.Series(grouped_entries_series.index, grouped_entries_series).sort_index()
		self._summarized_entries = self._summarized_entries[self._summarized_entries.index.values <= settings.SESSION_LENGTH]


	def run_simulation(self):
		'''
		Main function, which is called at the beginning of the simulation.
		It iterates over all traders in the time in which they arrive and trade.
		'''
		for timestamp, trader in self._summarized_entries.iteritems():
			self._regulator.current_time = timestamp
			self._regulator.remove_redundant_historic_exchanges()
			trader_executed_by_zerointelligence = trader.trade()
			self._regulator.add_current_exchanges_to_historic_exchanges()
			trader_executed_long, trader_executed_short = self._arbitrageur.hunt_and_kill()
			executed_traders_list = [trader_executed_by_zerointelligence, trader_executed_long, trader_executed_short]
			
			for executed_trader in executed_traders_list:
				if executed_trader is not None:
					self._list_zero_intelligence_traders[executed_trader].update_position_and_trades()
					self._list_zero_intelligence_traders[executed_trader].current_order = None