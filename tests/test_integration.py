import mock
import orderbook

import modules.regulator
import modules.settings as settings


def test_regulator_process_long_order_where_nbbo_ask_is_traders_order(basic_regulator,
    empty_orderbook, orderbook_with_best_bid_and_ask, basic_zerointelligence):
    '''
    If the NBBO is formed out of current trader's limit order, we need to check that he will ignore this order and trade
    as if the order were not there.
    '''
    basic_regulator._list_exchanges = [empty_orderbook, orderbook_with_best_bid_and_ask]
    basic_zerointelligence.current_order = modules.misc.CurrentOrder(
        idx = 1,
        side = 1,
        price = 1000,
        exchange = orderbook_with_best_bid_and_ask
    )
    basic_regulator.save_current_NBBO(10)