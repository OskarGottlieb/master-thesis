Readme TBD.



So far the logic of the modules is the following.
In the root directory `run.py` simply initiates the GOD object which then runs the whole simulation.
#TBD, run.py will specify the set of parameters, which will be then used in the simulation.

- Arbitrageur is an infinitely fast trader who reacts immediately to any arbitrage opportunities. Does not hold inventory.
- Asset is an exogenous variable, it's a stochastic mean-reverting time-series, which the traders trade.
- God is a wrapper of all other modules. He contains links to other modules and can therefore run the simulation.
- MarketMaker is a sophisticated trader, who submits orders on both sides of the market at once, does not have a private valuation of the asset.
- Misc (Miscellaneous) stores useful functions and objects which are used throught the whole project.
- Regulator oversees the exchanges and submits both up-to-date and lagged national best bid and offer (NBBO) information.
- Trader is a basis class for all trader objects, it contains attributes and methods used by all traders.
- ZeroIntelligence is a dummy trader, who trades the underlying asset according to his private and public valuation.
