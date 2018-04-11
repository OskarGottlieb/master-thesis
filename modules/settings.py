import math
import os


#Zero Intelligence Traders
ZERO_INTELLIGENCE_COUNT = int(66)
INTENSITY_ZERO_INTELLIGENCE = 0.005
QUANTITY_MAX = 10
SHADING_MIN = 0
SHADING_MAX = 0
SIGMA_UTILITY = math.sqrt(5e6)

# Market Makers
MARKET_MAKERS_COUNT = int(4)
INTENSITY_MARKET_MAKER = 0.0005
MARKET_MAKER_NUMBER_ORDERS = 5
MARKET_MAKER_NUMBER_OF_TICKS_BETWEEN_ORDERS = 100
MARKET_MAKER_SPREAD_AROUND_ASSET = 250

# Asset
INITIAL_ASSET_VALUE = 1e4
MEAN_REVERSION_FACTOR = 0.05
SIGMA_ASSET = math.sqrt(5e6)

# Market (General)
NAMES_OF_EXCHANGES = ('New York', 'Chicago')
NATIONAL_BEST_BID_AND_OFFER_DELAY = 300
TRADER_TYPES = ('Arbitrageur', 'MarketMaker', 'ZeroIntelligence')
SESSION_LENGTH = int(5e3)
PARAMETERS_SET = os.path.join(os.path.dirname(__file__), '..', 'parameters.csv')
BATCH_AUCTION_LENGTH = 300
INCLUDE_ARBITRAGEUR = False

# Sampling
SAMPLING_PRICE_SERIES = 200
PRELIMINARY_ANALYSIS_COUNT = 500
INSERT_INTO_DATABASE_FREQUENCY = 10

# Preliminary analysis
BASE_DICTIONARY = {
	'zero_intelligence_count': [200],
	'zero_intelligence_intensity': [0.005],
	'zero_intelligence_shading_min': [0],
	'zero_intelligence_shading_max': [0],
	'market_maker_count': [2],
	'market_maker_intensity': [0.0005],
	'market_maker_number_of_ticks_between_orders': [100],
	'market_maker_number_orders': [5],
	'market_maker_spread_around_asset': [250],
	'national_best_bid_and_offer_delay': [0],
	'batch_auction_length': [0],
	'session_length': [int(10e3)],
	'include_arbitrageur': [False]
}

#OTHER
PLOTLY_USERNAME = ''
PLOTLY_PASSWORD = ''

try:
	from modules.settings_dev import *
except ModuleNotFoundError:
	pass