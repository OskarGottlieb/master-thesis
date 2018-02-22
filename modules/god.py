from typing import List
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
		self._list_exchanges: List[orderbook.orderbook.NonUniqueIdOrderBook] = [orderbook.orderbook.NonUniqueIdOrderBook() for i in range(settings.EXCHANGES_COUNT)]
		self._regulator: modules.regulator.Regulator = modules.regulator.Regulator(
			NBBO_delay = settings.NBBO_DELAY,
			asset = self._asset,
			list_exchanges = self._list_exchanges
		)
		self._list_zero_intelligence_traders: List[modules.zerointelligence.ZeroIntelligence] = [modules.zerointelligence.ZeroIntelligence(
			idx = i,
			quantity_max = settings.QUANTITY_MAX,
			shading_min = settings.SHADING_MIN,
			shading_max = settings.SHADING_MAX,
			regulator = self._regulator,
			default_exchange = random.choice(self._list_exchanges),
		) for i in range(settings.ZERO_INTELLIGENCE_COUNT)]
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
			executed_trade_id = trader.trade(timestamp)
			if executed_trade_id is not None:
				self._list_zero_intelligence_traders[executed_trade_id].update_position_and_trades()
				self._list_zero_intelligence_traders[executed_trade_id].current_order = None
			self._regulator.save_current_NBBO(timestamp)
			self._arbitrageur.hunt_and_kill()

		#for trader in self._list_zero_intelligence_traders:
		#	print(len(trader.trades))
		print(sum([
			trader.calculate_total_payoff()
			for trader in self._list_zero_intelligence_traders
		]))
		