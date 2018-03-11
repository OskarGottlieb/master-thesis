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
INITIAL_ASSET_PRICE = 1e4
MEAN_REVERSION_FACTOR = 0.05
SIGMA_ASSET = math.sqrt(5e6)

# Market (General)
NAMES_OF_EXCHANGES = ('New York', 'Chicago')
NATIONAL_BEST_BID_AND_OFFER_DELAY = 0
TRADER_TYPES = ('Arbitrageur', 'MarketMaker', 'ZeroIntelligence')
SESSION_LENGTH = int(12e3)
PARAMETERS_SET = os.path.join(os.path.dirname(__file__), '..', 'parameters.csv')

try:
	from modules.settings_dev import *
except ModuleNotFoundError:
	pass