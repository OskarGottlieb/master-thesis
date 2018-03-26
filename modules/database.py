from typing import Any, List
import os
import pandas as pd
import psycopg2


import modules.settings as settings

'''
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


def insert_new_results(parameters_set_id:int, list_responses: List[Any]) -> None:
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


def get_parameters_table() -> None:
	'''
	Gets the database settings table.
	'''
	connection = connect_database()
	cursor = connection.cursor()
	query = f'SELECT * from settings'
	cursor.execute(query)
	settings_table = cursor.fetchall()
	# connection.commit()
	cursor.close()
	connection.close()

	return settings_table
