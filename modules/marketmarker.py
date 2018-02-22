from typing import List, Optional
import decimal
import math

import numpy as np
import pandas as pd

import modules.settings as settings
import modules.trader



class MarketMaker(modules.trader.Trader):
    def __init__(self, idx: int, quantity_max: int, shading_min: int, shading_max: int , *args, **kwargs):
        super(MarketMaker, self).__init__(*args, **kwargs)
        self._idx = idx
        self.quantity_max = quantity_max
        self.utility = []
        self.private_valuation = 0
        self.position = 0
        self.side: int = None
        self.shading_min: int = shading_min
        self.shading_max: int = shading_max
        
