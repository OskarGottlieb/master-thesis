import logwood
import multiprocessing
import os
import random
import pandas as pd

import modules.database
import modules.god
import modules.settings as settings



logwood.basic_config(level = logwood.WARNING)
		

def set_parameters_value(parameters: pd.DataFrame) -> None:
	parameters = parameters.to_dict('records')[0]
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
	settings.NATIONAL_BEST_BID_AND_OFFER_DELAY = 1000
	settings.BATCH_AUCTION_LENGTH = int(parameters['batch_auction_length'])
	settings.BATCH_AUCTION_LENGTH = 0
	settings.SESSION_LENGTH = int(parameters['session_length'])


def main() -> None:
	'''
	We get the set of parameters from which we select some set and we simulate it 10 times.
	After the simulation, we save the 10 results and continue with the simulation.
	'''
	parameters_table = modules.database.get_parameters_table()
	headers = pd.read_csv(settings.PARAMETERS_SET).columns.values
	parameters_dataframe = pd.DataFrame(parameters_table, columns = headers)
	list_ids_to_be_processed = [120]
	while True:
		parameters_set_id = random.choice(list_ids_to_be_processed)
		parameters = parameters_dataframe[parameters_dataframe['id'] == parameters_set_id].drop('id', 1)
		#set_parameters_value(parameters)
		list_responses = []
		for i in range(10):
			GOD = modules.god.God()
			list_responses.append(GOD.run_simulation())
		modules.database.insert_new_results(
			parameters_set_id = parameters_set_id,
		 	list_responses = list_responses
		)


if __name__ == '__main__':
	main()
	for process in range(4):
		process = multiprocessing.Process(target = main)
		process.start()
