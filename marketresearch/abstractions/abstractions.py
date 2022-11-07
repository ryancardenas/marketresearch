#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: abstractions
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/5/2022

Contains abstract classes for marketresearch project.
"""

from abc import ABC, abstractmethod


class AbstractAgent(ABC):
    """Abstract class representing the entity that makes decisions based on DataView and issues commands to a trading
    platform Client. Specifically, the Agent can send trade orders, request market data, and request account
    information through the Client. The Agent may be a simulated human being, an automated (closed loop) trading
    algorithm, a manual (open-loop) trading algorithm, a backtesting algorithm, or a data mining algorithm."""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def send_trade_order(self):
        """Sends a trader order to a Client."""
        pass

    @abstractmethod
    def request_market_data(self):
        """Requests market data from a Client."""
        pass

    @abstractmethod
    def request_account_info(self):
        """Requests account info from a Client."""
        pass


class AbstractClient(ABC):
    """Abstract class representing the software wrapper that handles trade orders, data requests, and account
    information requests through API calls. When used in simulations, the Client can interface with a Market model to
    execute orders, request market data, receive price action data, and receive trade receipts. When used in a trading
    algorithm, the Market layer is hidden from the Agent such that order execution and price action appear to occur
    inside the Client."""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def execute_trade_order(self):
        """Executes a trade order or delegates order execution to a Market model. When a Client is used for data
        mining, this method should be implemented without functionality (i.e. with a "pass" statement)."""
        pass

    @abstractmethod
    def request_market_data(self):
        """Requests market data, either from a Market model or from the Client's servers."""
        pass

    @abstractmethod
    def request_account_info(self):
        """Requests account info, either from a Market model or from the Client's servers.."""
        pass


class AbstractMarket(ABC):
    """Abstract class representing the entity that receives trade orders issued through the Client on behalf of an
    Agent, simulates price action, and generates trade receipts."""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def simulate_price_action(self):
        pass

    @abstractmethod
    def generate_trade_receipt(self):
        pass


class AbstractDataView(ABC):
    """Abstract class representing the handler that receives data packets and processes data, providing an interface
    for viewing the processed data. When used in simulation, each DataView receives market data directly from a
    Client. When used in backtesting, the DataView accesses market data stored in a database on disk or in the cloud.
    In all other use cases, the DataView receives market data that is validated and forwarded by the Agent. To submit
    market data to a DataView or request that a backtesting DataView step forward in time, an Agent or Client must call
    the DataView's update() method."""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def update(self):
        """Updates the DataView, either by assimilating new market data or by incrementing the time step used for
        accessing data from a database."""
        pass
