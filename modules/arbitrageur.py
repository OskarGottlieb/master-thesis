from typing import List, Optional

import modules.trader
import modules.regulator



class Arbitrageur(modules.trader.Trader):
	'''
	Arbitrageur represents an infinitely fast trader who profits from his superior speed by arbitraging the profit from
	the two exchanges.
	'''
	def __init__(self, *args, **kwargs) -> None:
		super(Arbitrageur, self).__init__(*args, **kwargs)


	def hunt_and_kill(self) -> Optional[List[int]]:
		'''
		The arbitrageur knows of the correct NBBO thanks to his infinite speed.
		If the condition of ask being below the bid is fulfilled, the Arbitrageur trades.
		'''
		national_best_bid_and_offer = self.get_accurate_national_best_bid_and_offer(
			current_orders = None,
			exchanges = self.regulator.historic_exchanges_list[0].exchanges,
		)
		if (national_best_bid_and_offer.bid and national_best_bid_and_offer.ask) and \
		(national_best_bid_and_offer.bid > national_best_bid_and_offer.ask):
			return self.trade_arbitrage(national_best_bid_and_offer)
		return {}


	def trade_arbitrage(self, national_best_bid_and_offer: modules.misc.NBBO) -> List[int]:
		'''
		Based on the state of the national_best_bid_and_offer, this funciton calls execute_order() two times for each exchange. 
		'''
		executed_traders_dict = {}
		for count, exchange_name in enumerate((national_best_bid_and_offer.bid_exchange, national_best_bid_and_offer.ask_exchange)):
			self.side = count
			executed_traders_dict.update(self.execute_order(
				exchange_name = exchange_name
			))
		return executed_traders_dict


	def calculate_total_surplus(self) -> float:
		'''
		At the end of trading, arbitrageur has a flat position and therefore only submits his total profit.
		'''
		return self.calculate_profit_from_trading()
