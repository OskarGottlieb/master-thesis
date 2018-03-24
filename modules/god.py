from typing import Any, List, NamedTuple
import itertools
import numpy as np
import pandas as pd
import logwood
import orderbook
import random

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
	marketmaker_surplus: float
	arbitrageur_profit: float
	bid_ask_spread_mean: float
	price_volatility: float
	price_discovery: float
	number_trades: int



class God:
	'''
	God knows everything and controls everything.
	'''
	def __init__(self) -> None:
		self._asset = modules.asset.Asset(settings.INITIAL_ASSET_VALUE, settings.MEAN_REVERSION_FACTOR, settings.SIGMA_ASSET)
		self._regulator: modules.regulator.Regulator = modules.regulator.Regulator(
			national_best_bid_and_offer_delay = settings.NATIONAL_BEST_BID_AND_OFFER_DELAY,
			asset = self._asset,
			batch_auction_length = settings.BATCH_AUCTION_LENGTH
		)
		self._list_zero_intelligence_traders: List[modules.zerointelligence.ZeroIntelligence] = [
			modules.zerointelligence.ZeroIntelligence(
				quantity_max = settings.QUANTITY_MAX,
				shading_min = settings.SHADING_MIN,
				shading_max = settings.SHADING_MAX,
				regulator = self._regulator,
				default_exchange = random.choice(list(self._regulator.exchanges.keys())),
			) for i in range(settings.ZERO_INTELLIGENCE_COUNT)
		]
		self._market_makers: List[modules.marketmaker.MarketMaker] = [
			modules.marketmaker.MarketMaker(
				regulator = self._regulator,
				exchange_name = random.choice(list(self._regulator.exchanges.keys())),
				number_of_orders = settings.MARKET_MAKER_NUMBER_ORDERS,
				ticks_between_orders = settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS,
				spread_around_asset = settings.MARKET_MAKER_SPREAD_AROUND_ASSET,
			) for i in range(settings.MARKET_MAKERS_COUNT)
		]
		self._arbitrageur = modules.arbitrageur.Arbitrageur(regulator = self._regulator)
		self._summarized_entries: pd.Series = pd.Series()
		self.summarize_entries()
		# In the end, we merge all traders into one list.
		self._all_traders: Dict[int: Any] = {
			trader._idx: trader for trader in self._list_zero_intelligence_traders + self._market_makers + [self._arbitrageur]
		}
		self.logger = logwood.get_logger(f'{self.__class__.__name__}')


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
		self._summarized_entries = pd.concat([zero_intelligence_entries, market_maker_entries, self._regulator.clearing_times]).sort_index()


	def process_exchange_responses(self) -> None:
		'''
		The wrapper module takes regulator's both dictionaries with responses of additions and executions and processes them
		by assigning the Orders to respective traders. The orders have already been executed on the respecitve exchange.
		'''
		if self._regulator.dict_regulator_responses_additions:
			for order in self._regulator.dict_regulator_responses_additions:
				self.logger.info(f'Processing \'A\' {order} by trader {self._regulator.meta[order].trader_idx}')
				self._all_traders[self._regulator.dict_regulator_responses_additions[order].trader_idx].current_orders.append(order)
		if self._regulator.dict_regulator_responses_executions:
			for order in self._regulator.dict_regulator_responses_executions:
				self.logger.info(
					f'''
						Executing {order} of {self._all_traders[self._regulator.meta
						[order].trader_idx].__class__.__name__} {self._regulator.meta[order].trader_idx}
					'''
				)
				trader = self._all_traders[self._regulator.dict_regulator_responses_executions[order].trader_idx]
				trader.update_position_and_trades(
		 			order = order
				)

		self._regulator.reset_regulator_information()


	def run_simulation(self):
		'''
		Main function, which is called at the beginning of the simulation.
		It iterates over all traders in the time in which they arrive and trade. It calls arbitrageur ad hoc, as he is checking
		the market for any arbitrage opportunities all the time.
		'''
		for timestamp, agent in self._summarized_entries.iteritems():
			self._regulator.current_time = timestamp
			self._regulator.asset.get_new_value(timestamp)
			self._regulator.remove_redundant_historic_exchanges()
			agent.do()
			# If the trading is continuous, clear after every agent's (MM/ZI) action.
			if self._regulator.continuous_trading:
				self._regulator.clear_orders_in_continuous_auction()
			self.process_exchange_responses()
			self._regulator.add_current_exchanges_to_historic_exchanges()
			self._arbitrageur.do()
			# If the trading is continuous, we need to clear again after every arbitrageur's action.
			if self._regulator.continuous_trading:
				self._regulator.clear_orders_in_continuous_auction()
				self.process_exchange_responses()


		self._regulator.calculate_sample_price_series()
		return GodResponse(
			mean_execution_time = np.mean(self._regulator.execution_times),
			zero_intelligence_surplus = sum([
				zero_intelligence_trader.calculate_total_surplus()
				for zero_intelligence_trader in self._list_zero_intelligence_traders
			]),
			marketmaker_surplus = sum([
				marketmaker.calculate_total_surplus()
				for marketmaker in self._market_makers
			]),
			arbitrageur_profit = self._arbitrageur.calculate_total_surplus(),
			bid_ask_spread_mean = self._regulator.calculate_mean_of_bid_ask_spread(),
			price_volatility = self._regulator.calculate_volatility(),
			price_discovery = 0,
			number_trades = self._regulator.total_number_of_trades
		)

