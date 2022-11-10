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
from typing import List, Optional, Union


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

    @abstractmethod
    def connect(self):
        """Establishes a connection between this interface and the data source. For a local file, this may mean loading
        data (or pointers) into memory. For a file located on a server, this may mean establishing a remote
        connection and downloading the file or opening lines of communication with the file."""
        pass

    @abstractmethod
    def update(self):
        """Updates the DataBase by saving new market data to disk."""
        pass


class AbstractCandlestickDataBase(AbstractDataBase):
    """A DataBase that provides OHLCTV data."""

    @abstractmethod
    def retrieve_dataset(self, symbol: str, timeframe: str, dataset: str):
        pass


class AbstractIndicator(ABC):
    """Abstract class representing a function that processes Timeframe data for a single Symbol and returns a value
    or array of values."""

    def __init__(self, name: str, parent: AbstractTimeframe):
        self.name = name
        self._parent = parent
        self._values = []

    @property
    @abstractmethod
    def values(self):
        pass

    @abstractmethod
    def update(self):
        """Updates the Indicator, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        pass


class AbstractTimeframe(ABC):
    """Abstract class representing the wrapper for data that is typically charted for a financial instrument. A
    Timeframe stores OHLC, timestamps, volume, and other data for a specific Instrument for a single aggregation
    period -- 1 Month, 1 Week, 1 Day, 1 Hour, 1 Min, etc. An Instrument may have many different Timeframes,
    but no more than one for each unique aggregation period."""

    def __init__(
        self,
        name: str,
        parent: AbstractInstrument,
        data_source: Optional[AbstractCandlestickDataBase] = None,
    ):
        self.name = name
        self._parent = parent
        if data_source is None:
            self._data_source = self._parent._data_source
        else:
            self._data_source = data_source
        self._indicators = {}
        self._protected_names = ["open", "high", "low", "close", "volume", "datetime"]
        self._connect_to_database()
        self.symbol = self._parent.name
        self._slice = slice(0, None)

    @property
    def indicators(self):
        """Returns a list of the names of each Indicator belonging to this object."""
        return list(self._indicators.keys())

    @property
    @abstractmethod
    def open(self):
        pass

    @property
    @abstractmethod
    def high(self):
        pass

    @property
    @abstractmethod
    def low(self):
        pass

    @property
    @abstractmethod
    def close(self):
        pass

    @property
    @abstractmethod
    def volume(self):
        pass

    @property
    @abstractmethod
    def datetime(self):
        pass

    @abstractmethod
    def update(self):
        """Updates the Timeframe, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        pass

    @abstractmethod
    def _connect_to_database(self):
        """Calls the linked DataBase's connect() method and performs any other setup operations needed."""
        pass

    def add_indicator(
        self, indicators: Union[AbstractIndicator, List[AbstractIndicator]]
    ):
        """Creates Indicator objects with their respective data sources and links them to this object, provided they
        don't already exist and are not duplicates of each other."""
        if not isinstance(indicators, List):
            indicators = [indicators]

        for indicator in indicators:
            if indicator.name in self.indicators:
                print(
                    f"DataFeed with name {indicator.name} is already linked! Skipping..."
                )
            elif indicator.name in self._protected_names:
                print(
                    f"Indicator name must not be any of {self._protected_names}. Skipping..."
                )
            else:
                self._indicators[indicator.name] = indicator

    def __getitem__(self, item: str):
        """Allows the Indicator objects to be accessed by 'MyTimeframe[indicator_name]' notation. If the Indicator
        has a protected name, then call the Timeframe property that the name refers to."""
        if isinstance(item, str):
            if item not in self.indicators:
                raise KeyError(f"{item} not found")
            elif item in self._protected_names:
                return getattr(self, item)
            else:
                return self._indicators[item].values
        else:
            raise KeyError(
                f"key must be a string representing the name of a linked Timeframe"
            )


class AbstractDataFeed(ABC):
    """Abstract class representing a data object that can be interacted with via a DataView. A DataFeed can be a
    financial instrument, news, account statistics, trade logs, or any other type of information that might be viewed
    through a DataView."""

    def __init__(self, name: str, data_source: AbstractDataBase):
        self.name = name
        self._data_source = data_source

    @property
    def dtype(self):
        """Retrieves the data type for this object."""
        return self.__class__

    @abstractmethod
    def update(self):
        """Updates the Instrument, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        pass

    @abstractmethod
    def _connect_to_database(self):
        """Calls the linked DataBase's connect() method and performs any other setup operations needed."""
        pass


class AbstractInstrument(AbstractDataFeed):
    """Abstract class representing a financial instrument data feed. This data feed can be an FX pair,
    futures contract, stock, option, or any other type of financial instrument."""

    def __init__(self, name: str, data_source: AbstractDataBase):
        super().__init__(name=name, data_source=data_source)
        self._timeframes = {}

    @property
    def timeframes(self):
        """Returns a list of the names of each Timeframe belonging to this object."""
        return list(self._timeframes.keys())

    @abstractmethod
    def update(self):
        """Updates the Instrument, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        pass

    @abstractmethod
    def _connect_to_database(self):
        """Calls the linked DataBase's connect() method and performs any other setup operations needed."""
        pass

    def add_timeframe(
        self, timeframes: Union[AbstractTimeframe, List[AbstractTimeframe]]
    ):
        """Creates Timeframe objects with their respective data sources and links them to this object, provided they
        don't already exist and are not duplicates of each other."""
        if not isinstance(timeframes, List):
            timeframes = [timeframes]

        for timeframe in timeframes:
            if timeframe.name in self.timeframes:
                print(
                    f"DataFeed with name {timeframe.name} is already linked! Skipping..."
                )
            else:
                self._timeframes[timeframe.name] = timeframe

    def __getitem__(self, item: str):
        """Allows the Timeframe objects to be accessed by 'MyInstrument[timeframe_name]' notation."""
        if isinstance(item, str):
            if item not in self.timeframes:
                raise KeyError(f"{item} not found")
            else:
                return self._timeframes[item]
        else:
            raise KeyError(
                f"key must be a string representing the name of a linked Timeframe"
            )


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

    @property
    def feeds(self):
        """Returns a list of the names of each DataFeed belonging to this object."""
        return list(self._feeds.keys())

    @abstractmethod
    def update(self):
        """Updates the DataView, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        pass

    def add_feed(self, feeds: Union[AbstractDataFeed, List[AbstractDataFeed]]):
        """Adds a DataFeed to this object, unless another DataFeed with the same name attribute is already linked."""
        if not isinstance(feeds, List):
            feeds = [feeds]

        for feed in feeds:
            if feed.name in self.feeds:
                print(f"DataFeed with name {feed.name} is already linked! Skipping...")
            else:
                self._feeds[feed.name] = feed

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
