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
	logger = logwood.get_logger('main')
	parameters_table = pd.DataFrame(
		modules.database.execute_query('SELECT * from settings;'),
		columns = ['id'] + list(settings.BASE_DICTIONARY.keys())
	)
	while True:
		settings_count = modules.database.get_settings_count()
		settings_count = settings_count[settings_count['response_count'] < settings.PRELIMINARY_ANALYSIS_COUNT]
		settings_id = random.choice(settings_count['settings_id'])
		parameters = parameters_table[parameters_table['id'] == settings_id]
		list_responses = []
		current_parameters_id = int(parameters.pop('id').iloc[0])
		set_parameters_value(parameters = parameters)
		for i in range(10):
			GOD = modules.god.God()
			list_responses.append(GOD.run_simulation())
			logger.warning(list_responses[-1])
		modules.database.insert_new_results(
			parameters_set_id = current_parameters_id,
		 	list_responses = list_responses
		)


if __name__ == '__main__':
	if len(sys.argv) > 1:
		if sys.argv[1] == 'analyze':
			analyzer = modules.analyzer.Analyzer()
	else:
		main()
		for process in range(2):
			process = multiprocessing.Process(target = main)
			process.start()
