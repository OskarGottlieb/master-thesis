from typing import Any, List, Optional, Tuple
import os
import pandas as pd
import psycopg2


import modules.settings as settings

'''
CREATE TABLE experiment(
	id SERIAL PRIMARY KEY,
	name varchar
);

CREATE TABLE experiment_content(
	experiment_id int REFERENCES experiment(id),
	settings_id int REFERENCES settings(id)
);

CREATE TABLE settings(
	id SERIAL PRIMARY KEY,
	zero_intelligence_count int,
	zero_intelligence_intensity real,
	zero_intelligence_shading_min int,
	zero_intelligence_shading_max int,
	market_maker_count int,
	market_maker_intensity real,
	market_maker_number_orders int,
	market_maker_number_of_ticks_between_orders int,
	market_maker_spread_around_asset int,
	national_best_bid_and_offer_delay int,
	batch_auction_length int,
	session_length int,
	include_arbitrageur bool
);

CREATE TABLE response(
	settings_id int REFERENCES settings(id),
	mean_execution_time real,
	zero_intelligence_surplus real,
	marketmaker_surplus real,
	arbitrageur_profit real,
	bid_ask_spread_mean real,
	price_volatility real,
	price_discovery real,
	number_trades int
);
'''



def connect_database(dbname: str = settings.DATABASE, user: str = settings.USER,
password: str = settings.PASSWORD, host: str = settings.SERVER, port: str = settings.PORT):
	conn = psycopg2.connect(
		dbname = dbname,
		user = user,
		password = password,
		host = host,
		port = port,
	)
	return conn


def fill_parameters_table(dataframe: pd.DataFrame = pd.DataFrame()) -> None:
	'''
	Fills the database settings table with the values which are stored in the csv file.
	'''
	connection = connect_database()
	cursor = connection.cursor()
	if dataframe.empty:
		dataframe = pd.read_csv(settings.PARAMETERS_SET)
	columns =  ','.join(dataframe.columns.values)
	query = f'INSERT INTO settings ({columns}) VALUES\n'
	for index, row in dataframe.iterrows():
		query += str(tuple(row)) + ',\n'
	query = query[:-2] + ';'
	cursor.execute(query)
	connection.commit()
	cursor.close()
	connection.close()


def insert_new_results(parameters_set_id: int, list_responses: List[Any]) -> None:
	connection = connect_database()
	cursor = connection.cursor()
	query = 'INSERT INTO response VALUES \n'
	responses = pd.DataFrame(list_responses)
	for index, row in responses.iterrows():
		query += str(tuple((parameters_set_id, )) + tuple(list(row))) + ',\n'
	query = query[:-2] + ';'
	cursor.execute(query)
	connection.commit()
	cursor.close()
	connection.close()


def execute_query(query: str) -> Optional[List[Tuple[Any]]]:
	'''
	Gets the database settings table.
	'''
	connection = connect_database()
	cursor = connection.cursor()
	cursor.execute(query)
	query_result = pd.DataFrame(
		cursor.fetchall(),
		columns = [description[0] for description in cursor.description]
	)
	cursor.close()
	connection.close()

	return query_result


def get_settings_count(unique: bool = False) -> pd.DataFrame:
	'''
	Gets the database settings table.
	'''
	query_result = execute_query(f'''
		SELECT settings.id as settings_id, (
			select count(*)
			from response
			where response.settings_id = settings.id
		) as response_count 
		from settings;
	''')
	if unique:
		pass 
	return query_result


def aggregate_settings() -> None:
	'''
	Gets the database settings table.
	'''
	query_result = execute_query(f'''
		SELECT settings.id,
		from settings
		group by
			zero_intelligence_count,
			zero_intelligence_intensity,
			zero_intelligence_shading_min,
			zero_intelligence_shading_max,
			market_maker_count,
			market_maker_intensity,
			market_maker_number_orders,
			market_maker_number_of_ticks_between_orders,
			market_maker_spread_around_asset,
			national_best_bid_and_offer_delay,
			batch_auction_length,
			session_length,
			include_arbitrageur
	''')
	
	return pd.DataFrame(query_result, columns = ('settings_id', 'response_count'))
	