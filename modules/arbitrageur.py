import sys

import modules.trader
import modules.regulator



class Arbitrageur(modules.trader.Trader):
	'''
	Arbitrageur represents an infinitely fast trader who profits from his superior speed by arbitraging the profit from
	the two exchanges.
	'''
	def __init__(self, *args, **kwargs) -> None:
		super(Arbitrageur, self).__init__(*args, **kwargs)


	def hunt_and_kill(self) -> None:
		'''
		The arbitrageur knows of the correct NBBO thanks to his infinite speed.
		'''
		national_best_bid_and_offer = self.regulator.list_NBBO[0]
		if (national_best_bid_and_offer.bid and national_best_bid_and_offer.ask) and \
		(national_best_bid_and_offer.bid > national_best_bid_and_offer.ask):
			print(national_best_bid_and_offer)
			sys.exit(1)