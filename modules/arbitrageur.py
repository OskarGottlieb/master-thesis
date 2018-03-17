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


	def do(self) -> None:
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
			self.trade_arbitrage(national_best_bid_and_offer)


	def trade_arbitrage(self, national_best_bid_and_offer: modules.misc.NBBO) -> None:
		'''
		Based on the state of the national_best_bid_and_offer, this funciton generates two orders which are routed to appropriate exchanges
		with the same (!) price.
		'''
		limit_price = int((national_best_bid_and_offer.bid + national_best_bid_and_offer.ask) / 2)
		for side, exchange_name in enumerate((national_best_bid_and_offer.bid_exchange, national_best_bid_and_offer.ask_exchange)):
			self.send_order_to_the_exchange(
				side = side,
				exchange_name = exchange_name,
				limit_price = limit_price
			)


	def calculate_total_surplus(self) -> float:
		'''
		At the end of trading, arbitrageur has a flat position and therefore only submits his total profit.
		'''
		return self.calculate_profit_from_trading()
