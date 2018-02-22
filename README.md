The purpose of this code is to do all my master thesis work for me.
So far the paper I'm reproducing is Welfare Effects of Market Making in Continuous.pdf

Once you have the requirements installed, you can go and simulate the dataseries by calling `python run.py`.

This function initiates the God object. 
This object knows about all other objects. On initialization it generates list of ZeroIntelligence traders.

The ZI traders enter the market according to a poisson process, at each time step the function trade() is called.
With a 50:50 chance the trader is either a buyer or seller, disregarding his previous position.
He also is limited as to the total position he can have at any time. With each trade he submits only one quantity.

The ZI trader also needs to know what his valuation is. His valuation is derived from a public and a private component.
Private component depends on a draw from a sorted normal random distribution. This ensures diminishing marginal utilitiy.

The draw from the distribution therefore depends on trader's intentions (buying and selling positions are right next to
one another) as well as on his overall position. 