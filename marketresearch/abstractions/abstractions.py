#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: abstractions
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/5/2022

Contains abstract classes for marketresearch project.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union, Tuple, Type

import pandas as pd


class AbstractDataBase(ABC):
    """Abstract class representing the interface between a source of data and a DataFeed or TimeFrame. A DataBase may
    source data from a file on disk or on a server. The scope of this class is limited to data sources that are
    files; it does not include online services that require API requests, such as TD Ameritrade or MetaTrader5. For
    accessing data through an API-configured online service, see AbstractClient."""

    def __init__(self, name: str, src_fn: Union[str, Path], file_mode: str = "r"):
        self.name = name
        self.src_fn = src_fn
        self.file_mode = file_mode
        self.f = None
        self.start_datetime = pd.to_datetime("1900")
        self.stop_datetime = pd.to_datetime("today")

    @abstractmethod
    def connect(self):
        """Establishes a connection between this interface and the data source. For a local file, this may mean loading
        data (or pointers) into memory. For a file located on a server, this may mean establishing a remote
        connection and downloading the file or opening lines of communication with the file."""
        pass

    @abstractmethod
    def update(self, args: Optional[dict] = None):
        """Updates the DataBase by saving new market data to disk."""
        pass


class AbstractCandlestickDataBase(AbstractDataBase):
    """A DataBase that provides OHLCTV data."""

    @abstractmethod
    def retrieve_dataset(self, symbol: str, timeframe: str, dataset: str):
        pass


class AbstractAgent(ABC):
    """Abstract class representing the entity that makes decisions based on DataView and issues commands to a trading
    platform Client. Specifically, the Agent can send trade orders, request market data, and request account
    information through the Client. The Agent may be a simulated human being, an automated (closed loop) trading
    algorithm, a manual (open-loop) trading algorithm, a backtesting algorithm, or a data mining algorithm."""

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

    def __init__(self):
        pass

    @abstractmethod
    def simulate_price_action(self):
        """Simulates price action."""
        pass

    @abstractmethod
    def generate_trade_receipt(self):
        """Generates trade receipts."""
        pass


class AbstractDataView(ABC):
    """Abstract class representing the handler that receives data packets and processes data, providing an interface
    for viewing the processed data. When used in simulation, each DataView receives market data directly from a
    Client. When used in backtesting, the DataView accesses market data stored in a database on disk or in the cloud.
    In all other use cases, the DataView receives market data that is validated and forwarded by the Agent. To submit
    market data to a DataView or request that a backtesting DataView step forward in time, an Agent or Client must call
    the DataView's update() method."""

    def __init__(self):
        self._feeds = {}
        self._start_datetime = pd.to_datetime("1900")
        self._stop_datetime = pd.to_datetime("today")

    @property
    def feeds(self):
        """Returns a list of the names of each DataFeed belonging to this object."""
        return list(self._feeds.keys())

    @property
    def start_datetime(self):
        return self._start_datetime

    @start_datetime.setter
    def start_datetime(self, value: Union[str, pd.Timestamp]):
        """Sets the start_datetime for this object and all children DataFeeds."""
        if isinstance(value, str):
            start_datetime = pd.to_datetime(value)
        elif isinstance(value, pd.Timestamp):
            start_datetime = value
        else:
            raise ValueError("datetime must be either str or pd.Timestamp")
        assert (
            start_datetime < self._stop_datetime
        ), "start_datetime must be less than stop_datetime"
        self._start_datetime = start_datetime
        self.update_feeds(
            args={"_start_datetime": self._start_datetime}, propogate=True
        )

    @property
    def stop_datetime(self):
        return self._stop_datetime

    @stop_datetime.setter
    def stop_datetime(self, value: Union[str, pd.Timestamp]):
        """Sets the stop_datetime for this object and all children DataFeeds."""
        if isinstance(value, str):
            stop_datetime = pd.to_datetime(value)
        elif isinstance(value, pd.Timestamp):
            stop_datetime = value
        else:
            raise ValueError("datetime must be either str or pd.Timestamp")
        assert (
            stop_datetime > self._start_datetime
        ), "stop_datetime must be greater than start_datetime"
        self._stop_datetime = stop_datetime
        self.update_feeds(args={"_stop_datetime": self._stop_datetime}, propogate=True)

    def update(self, args: Optional[dict] = None, propogate: bool = False):
        """Updates the DataView, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        if args is None:
            args = {}
        for attr, value in args.items():
            if not isinstance(attr, str):
                raise ValueError(
                    "attr must be a string representing an attribute of the DataView object"
                )
            else:
                if getattr(self, attr, False) and propogate:
                    setattr(self, attr, value)
                    self.update_feeds(args=args, propogate=True)
                elif getattr(self, attr, False):
                    setattr(self, attr, value)
                elif propogate:
                    self.update_feeds(args=args, propogate=True)
                else:
                    raise ValueError(
                        "args must be attribute of either this DataView object or its child DataFeeds"
                    )

    def update_feeds(self, args: Optional[dict] = None, propogate: bool = False):
        """Updates all child DataFeeds with the specified value at the specified attribute."""
        for name, obj in self._feeds.items():
            obj.update(args=args, propogate=propogate)

    def add_feeds(self, feeds: List[Tuple[str, Type[AbstractDataFeed], dict]]):
        """Adds a DataFeed to this object, unless another DataFeed with the same name attribute is already linked."""
        for class_type, args in feeds:
            assert "name" in args.keys(), "'name' must be defined for each DataFeed"
            name = args["name"]
            if name in self.feeds:
                print(f"DataFeed with name {name} is already linked! Skipping...")
            else:
                feed = class_type(parent=self, **args)
                self._feeds[name] = feed

    def __getitem__(self, item: str):
        """Allows the DataFeed objects to be accessed by 'MyDataView[feed_name]' notation."""
        if isinstance(item, str):
            if item not in self.feeds:
                raise KeyError(f"{item} not found")
            else:
                return self._feeds[item]
        else:
            raise KeyError(
                f"key must be a string representing the name of a linked DataFeed"
            )


class AbstractDataFeed(ABC):
    """Abstract class representing a data object that can be interacted with via a DataView. A DataFeed can be a
    financial instrument, news, account statistics, trade logs, or any other type of information that might be viewed
    through a DataView."""

    def __init__(
        self, name: str, parent: AbstractDataView, data_source: AbstractDataBase
    ):
        self.name = name
        self._parent = parent
        self._data_source = data_source
        self._start_datetime = self._parent.start_datetime
        self._stop_datetime = self._parent.stop_datetime
        self._connect_to_database()

    @property
    def dtype(self):
        """Retrieves the data type for this object."""
        return self.__class__

    @property
    def start_datetime(self):
        return self._start_datetime

    @property
    def stop_datetime(self):
        return self._stop_datetime

    @abstractmethod
    def update(self, args: Optional[dict] = None, propogate: bool = False):
        """Updates this DataFeed and its child DataBase."""
        if args is None:
            args = {}
        for attr, value in args.items():
            if not isinstance(attr, str):
                raise ValueError(
                    "attr must be a string representing an attribute of this object"
                )
            else:
                setattr(self, attr, value)

    def _connect_to_database(self):
        """Calls the linked DataBase's connect() method and performs any other setup operations needed."""
        self._data_source.connect()
