#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: data_enums
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/5/2022

Enumerations for data types according to MetaTrader5 documentation. For naming of enumeration classes, snake case is
used instead of camel case in order to maintain consistency and readability with MetaTrader5 documentation.
"""

import enum


class ENUM_ORDER_TYPE(enum.Enum):
    """
    ORDER_TYPE_BUY - Market Buy order
    ORDER_TYPE_SELL - Market Sell order
    ORDER_TYPE_BUY_LIMIT - Buy Limit pending order
    ORDER_TYPE_SELL_LIMIT - Sell Limit pending order
    ORDER_TYPE_BUY_STOP - Buy Stop pending order
    ORDER_TYPE_SELL_STOP - Sell Stop pending order
    ORDER_TYPE_BUY_STOP_LIMIT - Upon reaching the order price, a pending Buy Limit order is placed at the
        StopLimit price
    ORDER_TYPE_SELL_STOP_LIMIT - Upon reaching the order price, a pending Sell Limit order is placed at the
    StopLimit price
    ORDER_TYPE_CLOSE_BY - Order to close a position by an opposite one
    """

    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5
    BUY_STOP_LIMIT = 6
    SELL_STOP_LIMIT = 7
    CLOSE_BY = 8


class ENUM_ORDER_STATE(enum.Enum):
    """
    ORDER_STATE_STARTED - Order checked, but not yet accepted by broker
    ORDER_STATE_PLACED - Order accepted
    ORDER_STATE_CANCELED - Order canceled by client
    ORDER_STATE_PARTIAL - Order partially executed
    ORDER_STATE_FILLED - Order fully executed
    ORDER_STATE_REJECTED - Order rejected
    ORDER_STATE_EXPIRED - Order expired
    ORDER_STATE_REQUEST_ADD - Order is being registered (placing to the trading system)
    ORDER_STATE_REQUEST_MODIFY - Order is being modified (changing its parameters)
    ORDER_STATE_REQUEST_CANCEL - Order is being deleted (deleting from the trading system)
    """

    STARTED = 0
    PLACED = 1
    CANCELED = 2
    PARTIAL = 3
    FILLED = 4
    REJECTED = 5
    EXPIRED = 6
    REQUEST_ADD = 7
    REQUEST_MODIFY = 8
    REQUEST_CANCEL = 9


class ENUM_ORDER_TYPE_FILLING(enum.Enum):
    """
    Fill or Kill - An order can be executed in the specified volume only. If the necessary amount of a financial
        instrument is currently unavailable in the market, the order will not be executed. The desired volume can
        be made up of several available offers. The possibility of using FOK orders is determined at the trade
        server.
    Immediate or Cancel - A trader agrees to execute a deal with the volume maximally available in the market
        within that indicated in the order. If the request cannot be filled completely, an order with the
        available volume will be executed, and the remaining volume will be canceled. The possibility of using
        IOC orders is determined at the trade server.
    Return - In case of partial filling, an order with remaining volume is not canceled but processed further.
        Return orders are not allowed in the Market Execution mode (market execution —
        SYMBOL_TRADE_EXECUTION_MARKET).
    """

    FILL_OR_KILL = 0
    IMMEDIATE_OR_CANCEL = 1
    RETURN = 2


class ENUM_ORDER_TYPE_TIME(enum.Enum):
    """
    GTC - Good till cancel order
    DAY - Good till current trade day order
    SPECIFIED - Good till expired order
    SPECIFIED_DAY - The order will be effective till 23:59:59 of the specified day. If this time is outside a
        trading session, the order expires in the nearest trading time.
    """

    GTC = 0
    DAY = 1
    SPECIFIED = 2
    SPECIFIED_DAY = 3


class ENUM_ORDER_REASON(enum.Enum):
    """
    ORDER_REASON_CLIENT - The order was placed from a desktop terminal
    ORDER_REASON_MOBILE - The order was placed from a mobile application
    ORDER_REASON_WEB - The order was placed from a web platform
    ORDER_REASON_EXPERT - The order was placed from an MQL5-program, i.e. by an Expert Advisor or a script
    ORDER_REASON_SL - The order was placed as a result of Stop Loss activation
    ORDER_REASON_TP - The order was placed as a result of Take Profit activation
    ORDER_REASON_SO - The order was placed as a result of the Stop Out event
    """

    CLIENT = 0
    MOBILE = 1
    WEB = 2
    EXPERT = 3
    SL = 4
    TP = 5
    SO = 6


class ENUM_DEAL_TYPE(enum.Enum):
    """
    DEAL_TYPE_BUY - Buy
    DEAL_TYPE_SELL - Sell
    DEAL_TYPE_BALANCE - Balance
    DEAL_TYPE_CREDIT - Credit
    DEAL_TYPE_CHARGE - Additional charge
    DEAL_TYPE_CORRECTION - Correction
    DEAL_TYPE_BONUS - Bonus
    DEAL_TYPE_COMMISSION - Additional commission
    DEAL_TYPE_COMMISSION_DAILY - Daily commission
    DEAL_TYPE_COMMISSION_MONTHLY - Monthly commission
    DEAL_TYPE_COMMISSION_AGENT_DAILY - Daily agent commission
    DEAL_TYPE_COMMISSION_AGENT_MONTHLY - Monthly agent commission
    DEAL_TYPE_INTEREST - Interest rate
    DEAL_TYPE_BUY_CANCELED - Canceled buy deal. There can be a situation when a previously executed buy deal is
        canceled. In this case, the type of the previously executed deal (DEAL_TYPE_BUY) is changed to
        DEAL_TYPE_BUY_CANCELED, and its profit/loss is zeroized. Previously obtained profit/loss is
        charged/withdrawn using a separated balance operation
    DEAL_TYPE_SELL_CANCELED - Canceled sell deal. There can be a situation when a previously executed sell deal is
        canceled. In this case, the type of the previously executed deal (DEAL_TYPE_SELL) is changed to
        DEAL_TYPE_SELL_CANCELED, and its profit/loss is zeroized. Previously obtained profit/loss is
        charged/withdrawn using a separated balance operation
    DEAL_DIVIDEND - Dividend operations
    DEAL_DIVIDEND_FRANKED - Franked (non-taxable) dividend operations
    DEAL_TAX - Tax charges
    """

    BUY = 0
    SELL = 1
    BALANCE = 2
    CREDIT = 3
    CHARGE = 4
    CORRECTION = 5
    BONUS = 6
    COMMISSION = 7
    COMMISSION_DAILY = 8
    COMMISSION_MONTHLY = 9
    COMMISSION_AGENT_DAILY = 10
    COMMISSION_AGENT_MONTHLY = 11
    INTEREST = 12
    BUY_CANCELED = 13
    SELL_CANCELED = 14
    DIVIDEND = 15
    DIVIDEND_FRANKED = 16
    TAX = 17


class ENUM_DEAL_ENTRY(enum.Enum):
    """
    DEAL_ENTRY_IN - Entry in
    DEAL_ENTRY_OUT - Entry out
    DEAL_ENTRY_INOUT - Reverse
    DEAL_ENTRY_OUT_BY - Close a position by an opposite one
    """

    IN = 0
    OUT = 1
    INOUT = 2
    OUT_BY = 3


class ENUM_DEAL_REASON(enum.Enum):
    """
    DEAL_REASON_CLIENT - The deal was executed as a result of activation of an order placed from a desktop terminal
    DEAL_REASON_MOBILE - The deal was executed as a result of activation of an order placed from a mobile application
    DEAL_REASON_WEB - The deal was executed as a result of activation of an order placed from the web platform
    DEAL_REASON_EXPERT - The deal was executed as a result of activation of an order placed from an MQL5 program,
        i.e. an Expert Advisor or a script
    DEAL_REASON_SL - The deal was executed as a result of Stop Loss activation
    DEAL_REASON_TP - The deal was executed as a result of Take Profit activation
    DEAL_REASON_SO - The deal was executed as a result of the Stop Out event
    DEAL_REASON_ROLLOVER - The deal was executed due to a rollover
    DEAL_REASON_VMARGIN - The deal was executed after charging the variation margin
    DEAL_REASON_SPLIT - The deal was executed after the split (price reduction) of an instrument, which had an open
        position during split announcement
    """

    CLIENT = 0
    MOBILE = 1
    WEB = 2
    EXPERT = 3
    SL = 4
    TP = 5
    SO = 6
    ROLLOVER = 7
    VMAGIN = 8
    SPLIT = 9
