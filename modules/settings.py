import math

ZERO_INTELLIGENCE_COUNT = int(66)
MARKET_MAKERS_COUNT = int(10)
NAMES_OF_EXCHANGES = ('New York', 'Chicago')
SESSION_LENGTH = int(12e3)
INTENSITY_ZERO_INTELLIGENCE = 0.005
INTENSITY_MARKET_MAKER = 0.0005
POISSON_STEP = int(1e5)

INITIAL_ASSET_PRICE = 1e4
MEAN_REVERSION_FACTOR = 0.05
SIGMA_ASSET = math.sqrt(5e6)
SIGMA_UTILITY = math.sqrt(5e6)
QUANTITY_MAX = 10
SHADING_MIN = 0
SHADING_MAX = 0

NATIONAL_BEST_BID_AND_OFFER_DELAY = 100

TRADER_TYPES = ('Arbitrageur', 'MarketMaker', 'ZeroIntelligence')