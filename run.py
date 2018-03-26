import logwood
import multiprocessing
import os
import sys
import random
import pandas as pd

import modules.analyzer
import modules.database
import modules.god
import modules.settings as settings



logwood.basic_config(level = logwood.WARNING)
		

def set_parameters_value(parameters: pd.DataFrame) -> None:
	settings.ZERO_INTELLIGENCE_COUNT = int(parameters['zero_intelligence_count'])
	settings.INTENSITY_ZERO_INTELLIGENCE = parameters['zero_intelligence_intensity']
	settings.SHADING_MIN = int(parameters['zero_intelligence_shading_min'])
	settings.SHADING_MAX = int(parameters['zero_intelligence_shading_max'])
	settings.MARKET_MAKERS_COUNT = int(parameters['market_maker_count'])
	settings.INTENSITY_MARKET_MAKER = parameters['market_maker_intensity']
	settings.MARKET_MAKER_NUMBER_ORDERS = int(parameters['market_maker_number_orders'])
	settings.MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS = int(parameters['market_maker_number_of_ticks_between_orders'])
	settings.MARKET_MAKER_SPREAD_AROUND_ASSET = int(parameters['market_maker_spread_around_asset'])
	settings.NATIONAL_BEST_BID_AND_OFFER_DELAY = int(parameters['national_best_bid_and_offer_delay'])
	settings.BATCH_AUCTION_LENGTH = int(parameters['batch_auction_length'])
	settings.SESSION_LENGTH = int(parameters['session_length'])
	settings.INCLUDE_ARBITRAGEUR = int(parameters['include_arbitrageur'])


def main() -> None:
	'''
	We get the set of parameters from which we select some set and we simulate it 10 times.
	After the simulation, we save the 10 results and continue with the simulation.
	'''
	parameters_table = pd.DataFrame(
		modules.database.get_parameters_table(),
		columns = ['id'] + list(settings.BASE_DICTIONARY.keys())
	)
	for index, row in parameters_table.iterrows():
		current_parameters_id = row.pop('id')
		parameters = row.to_dict()
		set_parameters_value(parameters = parameters)
		
		list_responses = []
		for i in range(1, settings.PRELIMINARY_ANALYSIS_COUNT + 1):
			GOD = modules.god.God()
			list_responses.append(GOD.run_simulation())
			print(list_responses[-1])
			if i % settings.INSERT_INTO_DATABASE_FREQUENCY == 0:
				modules.database.insert_new_results(
					parameters_set_id = current_parameters_id,
				 	list_responses = list_responses
				)
				list_responses = []


if __name__ == '__main__':
	if len(sys.argv) > 1:
		if sys.argv[1] == 'analyze':
			analyzer = modules.analyzer.Analyzer()
	else:
		main()
		for process in range(4):
			process = multiprocessing.Process(target = main)
			process.start()
