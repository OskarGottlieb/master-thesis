from typing import Any, List, NamedTuple
import itertools
import random
import numpy as np
import pandas as pd
import orderbook

import modules.asset
import modules.arbitrageur
import modules.marketmaker
import modules.regulator
import modules.settings as settings
import modules.zerointelligence



class GodResponse(NamedTuple):
	'''
	God response gives us metrics which we then use to 
	'''
	mean_execution_time: float
	zero_intelligence_surplus: float
	arbitrageur_profit: float



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
		self._market_makers: List[modules.marketmaker.MarketMaker] = [
			modules.marketmaker.MarketMaker(
				idx = i,
				regulator = self._regulator,
				default_exchange = random.choice(list(self._regulator.exchanges.keys())),
			) for i in range(settings.MARKET_MAKERS_COUNT)
		]
		self._arbitrageur = modules.arbitrageur.Arbitrageur(regulator = self._regulator, idx = 1)
		self._summarized_entries: pd.Series = None
		self.summarize_entries()


	def generate_entries(self, traders_list: List[Any],	intensity_of_poisson_process: float, traders_count: int) -> pd.Series:
		'''
		Creates a grouped series equal in length to the number of zerointelligence traders times the session length.
		Then randomly (with equal probability) assigns a value to the given trader.
		It cuts all traders above the original length of the session length.
		'''
		summarized_entries_times = np.random.exponential(1 / intensity_of_poisson_process, settings.SESSION_LENGTH * traders_count)
		grouped_entries_series = pd.Series(
			index = np.random.choice(traders_list, settings.SESSION_LENGTH * traders_count),
			data = summarized_entries_times
		).groupby(level = 0).cumsum()
		summarized_entries = pd.Series(grouped_entries_series.index, grouped_entries_series)
		return summarized_entries[summarized_entries.index.values <= settings.SESSION_LENGTH]


	def summarize_entries(self) -> None:
		'''
		Creates two pandas Series out of the two trader types which arrive according to their own poisson process.
		It then merges the two series and sorts them by the index.
		'''
		zero_intelligence_entries = self.generate_entries(
			traders_list = self._list_zero_intelligence_traders,
			traders_count = settings.ZERO_INTELLIGENCE_COUNT,
			intensity_of_poisson_process = settings.INTENSITY_ZERO_INTELLIGENCE,
		)
		market_maker_entries = self.generate_entries(
			traders_list = self._market_makers,
			traders_count = settings.MARKET_MAKERS_COUNT,
			intensity_of_poisson_process = settings.INTENSITY_MARKET_MAKER,
		)
		self._summarized_entries = pd.concat([zero_intelligence_entries, market_maker_entries]).sort_index()


	def run_simulation(self):
		'''
		Main function, which is called at the beginning of the simulation.
		It iterates over all traders in the time in which they arrive and trade. It calls arbitrageur ad hoc, as he is checking
		the market for any arbitrage opportunities all the time.
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
		

		return GodResponse(
			mean_execution_time = np.mean(self._regulator.execution_times),
			zero_intelligence_surplus = sum([
				zero_intelligence_trader.calculate_total_surplus()
				for zero_intelligence_trader in self._list_zero_intelligence_traders
			]),
			arbitrageur_profit = self._arbitrageur.calculate_total_surplus()
		)

