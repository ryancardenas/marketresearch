#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: backtesting
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/12/2022

DataViews used for backtesting.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import functools
from typing import List, Optional, Tuple, Type

import numpy as np
import pandas as pd

import marketresearch.abstractions.abstractions as abmr


class BacktestDataView(abmr.AbstractDataView):
    """Class representing the handler for market data in a backtesting scenario."""

    def __init__(self):
        super().__init__()


@functools.total_ordering
class BacktestTimeframe(ABC):
    """Abstract class representing the wrapper for data that is typically charted for a financial instrument. A
    Timeframe stores OHLC, timestamps, volume, and other data for a specific Instrument for a single aggregation
    period -- 1 Month, 1 Week, 1 Day, 1 Hour, 1 Min, etc. An Instrument may have many different Timeframes,
    but no more than one for each unique aggregation period."""

    def __init__(
        self,
        name: str,
        parent: BacktestInstrument,
        data_source: Optional[abmr.AbstractCandlestickDataBase] = None,
    ):
        assert name[0] in ["M", "W", "D", "H", "m"]
        assert 2 <= len(name) <= 3
        assert 0 < int(name[1:]) < 100
        self.name = name
        self._parent = parent
        self.symbol = self._parent.name
        self._start_datetime = self._parent.start_datetime
        self._stop_datetime = self._parent.stop_datetime
        if data_source is None:
            self._data_source = self._parent._data_source
        else:
            self._data_source = data_source
        self._indicators = {}
        self._protected_names = ["open", "high", "low", "close", "volume", "datetime"]
        self._connect_to_database()
        self._get_all_datetimes()
        self._timeframe_values = {
            "M": 30.0,
            "W": 7.0,
            "D": 1.0,
            "H": 1 / 24,
            "m": 1 / 1440,
        }

    @property
    def start_datetime(self):
        return self._start_datetime

    @property
    def stop_datetime(self):
        return self._stop_datetime

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

    def _get_all_datetimes(self):
        vals = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="timestamp",
        )
        self._all_datetimes = pd.to_datetime(vals[:])

    def _update_slice(self):
        datetime = self._all_datetimes
        assert (
            datetime[-1] > self._start_datetime
        ), f"{self.name} datetimes terminate before _start_datetime"
        assert (
            datetime[-1] >= self._stop_datetime
        ), f"{self.name} datetimes terminate before _stop_datetime"
        assert (
            datetime[0] < self._stop_datetime
        ), f"{self.name} datetimes begin after _stop_datetime"
        start_idx = np.where(datetime > self._start_datetime)[0][0]
        stop_idx = np.where(datetime > self._stop_datetime)[0][0]
        self._slice = slice(start_idx, stop_idx)

    def update(self, args: Optional[dict] = None, propogate: bool = False):
        """Updates the Timeframe, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        if args is None:
            args = {}
        for attr, value in args.items():
            if not isinstance(attr, str):
                raise ValueError(
                    "attr must be a string representing an attribute of this object"
                )
            else:
                setattr(self, attr, value)
        if propogate:
            self._update_slice()

    def update_indicators(self, args: Optional[dict] = None):
        """Updates all child Indicators with the specified value at the specified attribute."""
        if args is None:
            args = {}
        for attr, value in args.items():
            if not isinstance(attr, str):
                raise ValueError(
                    "attr must be a string representing an attribute of all child Indicators"
                )
            else:
                for name, obj in self._indicators.items():
                    setattr(obj, attr, value)

    def _connect_to_database(self):
        """Calls the linked DataBase's connect() method and performs any other setup operations needed."""
        self._data_source.connect()

    def add_indicators(self, indicators: List[Tuple[Type[AbstractIndicator], dict]]):
        """Creates Indicator objects with their respective data sources and links them to this object, provided they
        don't already exist and are not duplicates of each other."""
        for indicator_class, args in indicators:
            indicator = indicator_class(parent=self, **args)
            if indicator.name in self.indicators:
                print(
                    f"Indicator with name {indicator.name} is already linked! Skipping..."
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
            if item in self.indicators:
                return self._indicators[item].values
            elif item in self._protected_names:
                return getattr(self, item)
            else:
                raise KeyError(f"{item} not found")
        else:
            raise KeyError(
                f"key must be a string representing the name of a linked Timeframe"
            )

    @property
    def _value(self):
        """Determines the 'value' of this Timeframe for comparison against other Timeframes."""
        val = self._timeframe_values[self.name[0]]
        val *= int(self.name[1:])
        return val

    def __lt__(self, obj: BacktestTimeframe):
        """Determines if this Timeframe is 'less than' another Timeframe."""
        return self._value < obj._value

    def __gt__(self, obj: BacktestTimeframe):
        """Determines if this Timeframe is 'greater than' another Timeframe."""
        return self._value > obj._value

    def __le__(self, obj: BacktestTimeframe):
        """Determines if this Timeframe is 'less than or equal to' another Timeframe."""
        return self._value <= obj._value

    def __ge__(self, obj: BacktestTimeframe):
        """Determines if this Timeframe is 'greater than or equal to' another Timeframe."""
        return self._value >= obj._value

    def __eq__(self, obj: BacktestTimeframe):
        """Determines if this Timeframe is 'equal to' another Timeframe."""
        return self._value == obj._value


class BacktestInstrument(abmr.AbstractDataFeed):
    """Abstract class representing a financial instrument data feed. This data feed can be an FX pair,
    futures contract, stock, option, or any other type of financial instrument."""

    def __init__(
        self, name: str, parent: BacktestDataView, data_source: abmr.AbstractDataBase
    ):
        super().__init__(name=name, parent=parent, data_source=data_source)
        self._timeframes = {}
        self._default_timeframe_class = None

    @property
    def timeframes(self):
        """Returns a list of the names of each Timeframe belonging to this object."""
        return list(self._timeframes.keys())

    def update(self, args: Optional[dict] = None, propogate: bool = False):
        """Updates this Instrument and its child Timeframes."""
        if args is None:
            args = {}
        for attr, value in args.items():
            if not isinstance(attr, str):
                raise ValueError(
                    "attr must be a string representing an attribute of the Instrument object"
                )
            else:
                if getattr(self, attr, False):
                    setattr(self, attr, value)
                elif propogate:
                    self.update_timeframes(args=args, propogate=True)
                else:
                    raise ValueError(
                        "args must be attribute of either this Instrument object or its child Timeframes"
                    )

    def update_timeframes(self, args: Optional[dict] = None, propogate: bool = False):
        """Updates all child Timeframes with the specified value at the specified attribute."""
        for name, obj in self._timeframes.items():
            obj.update(args=args, propogate=propogate)

    def add_timeframes(self, timeframes: dict):
        """Creates Timeframe objects with their respective data sources and links them to this object, provided they
        don't already exist and are not duplicates of each other."""
        for name, args in timeframes.items():
            if name in self.timeframes:
                print(f"Timeframe with name {name} is already linked! Skipping...")
            else:
                timeframe = self._default_timeframe_class(
                    name=name, parent=self, **args
                )
                self._timeframes[name] = timeframe

    def add_indicators(self, indicators: List[Tuple[Type[AbstractIndicator], dict]]):
        for key in self.timeframes:
            self._timeframes[key].add_indicators(indicators=indicators)

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


class FxTimeframe(BacktestTimeframe):
    """A Timeframe object for foreign exchange currency pairs, which have more attributes than an AbstractTimeframe."""

    def __init__(
        self,
        name: str,
        parent: BacktestInstrument,
        data_source: Optional[abmr.AbstractDataBase] = None,
    ):
        super().__init__(name=name, parent=parent, data_source=data_source)
        self._update_slice()

    @property
    def open(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="open",
        )
        return dataset[self._slice]

    @property
    def high(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="high",
        )
        return dataset[self._slice]

    @property
    def low(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="low",
        )
        return dataset[self._slice]

    @property
    def close(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="close",
        )
        return dataset[self._slice]

    @property
    def volume(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="tickvol",
        )
        return dataset[self._slice]

    @property
    def datetime(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="timestamp",
        )
        return pd.to_datetime(dataset[self._slice])


class FxInstrument(BacktestInstrument):
    """An Instrument object for foreign exchange currency pairs."""

    def __init__(
        self,
        name: str,
        parent: BacktestDataView,
        data_source: abmr.AbstractDataBase,
    ):
        super().__init__(name=name, parent=parent, data_source=data_source)
        self._timeframes = {}
        self._default_timeframe_class = FxTimeframe


class AbstractIndicator(ABC):
    """Abstract class representing a function that processes Timeframe data for a single Symbol and returns a value
    or array of values."""

    def __init__(self, name: str, parent: BacktestTimeframe, dataset_name: str):
        self.name = name
        self.dataset_name = dataset_name
        self._parent = parent
        self._values = []

    @property
    @abstractmethod
    def values(self):
        pass

    @abstractmethod
    def _init_compute(self):
        """Initializes the Indicator with values computed based on all currently available values in the parent's
        dataset."""
        pass

    @abstractmethod
    def update(self):
        """Updates the Indicator with a single value computed based on the most recent values in the parent's
        dataset."""
        pass