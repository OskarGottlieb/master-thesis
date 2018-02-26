from typing import List, Optional
import decimal
import math

import numpy as np
import pandas as pd

import modules.settings as settings
import modules.trader



class MarketMaker(modules.trader.Trader):
	def __init__(self, default_exchange:str, *args, **kwargs):
		super(MarketMaker, self).__init__(*args, **kwargs)
		self.default_exchange = default_exchange
		
