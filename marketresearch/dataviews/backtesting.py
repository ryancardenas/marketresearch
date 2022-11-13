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
from typing import List, Optional, Tuple, Type, Union

import numpy as np
import pandas as pd

import marketresearch.abstractions.abstractions as abmr


class BacktestDataView(abmr.AbstractDataView):
    """Class representing the handler for market data in a backtesting scenario."""

    def __init__(self):
        super().__init__()
        self._min_datetime = self.start_datetime
        self._max_datetime = self.stop_datetime

    def step_forward(self, timedelta: Union[str, pd.Timedelta]):
        if isinstance(timedelta, str):
            timedelta = pd.Timedelta(timedelta)
        new_datetime = self.stop_datetime + timedelta
        if new_datetime <= self._max_datetime:
            self.stop_datetime = new_datetime
            return 1
        else:
            print("forward step would exceed max available datetime; ignoring request")
            return 0


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
        self._all_datetimes = self._get_all_datetimes()
        self._timeframe_values = {
            "M": 28.0 * 10080.0,
            "W": 10080.0,
            "D": 1440.0,
            "H": 60.0,
            "m": 1.0,
        }
        self._slice = slice(0, None)
        self._smart_bar_slice = slice(-1, -1)
        self.timedelta = self._initialize_timedelta()

    def _initialize_timedelta(self):
        char = self.name[0]
        basenum = int(self.name[1:])
        num = basenum * self._timeframe_values[char]
        return pd.Timedelta(f"{num}m")

    @property
    def start_datetime(self):
        return self._start_datetime

    @property
    def stop_datetime(self):
        return self._stop_datetime

    @property
    def smallest_timedelta(self):
        min_tf_name = self._parent.smallest_timeframe
        min_tf = self._parent._timeframes[min_tf_name]
        return min_tf.timedelta

    @property
    def is_smallest_timeframe(self):
        return self.timedelta == self.smallest_timedelta

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
        return pd.to_datetime(vals[:])

    def _update_slice(self, initial_update: bool = False):
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
        stop_idx = np.where(datetime > self._stop_datetime - self.timedelta)[0][0]
        self._slice = slice(start_idx, stop_idx)
        if not initial_update:
            self._update_smart_bar_slice()

    def _update_smart_bar_slice(self):
        if self.is_smallest_timeframe:
            self._smart_bar_slice = slice(-1, -1)
        else:
            min_tf_name = self._parent.smallest_timeframe
            min_tf = self._parent._timeframes[min_tf_name]
            small_datetime = min_tf._all_datetimes

            start_datetime = self._all_datetimes[self._slice.stop]
            start_idx = np.where(small_datetime >= start_datetime)[0][0]
            stop_idx = min_tf._slice.stop
            self._smart_bar_slice = slice(start_idx, stop_idx)

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


class FxTimeframe(BacktestTimeframe):
    """A Timeframe object for foreign exchange currency pairs, which have more attributes than an AbstractTimeframe."""

    def __init__(
        self,
        name: str,
        parent: BacktestInstrument,
        data_source: Optional[abmr.AbstractDataBase] = None,
    ):
        super().__init__(name=name, parent=parent, data_source=data_source)
        self._update_slice(initial_update=True)

    @property
    def open(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="open",
        )
        smart_bar = np.array([])
        if not self.is_smallest_timeframe:
            min_tf_name = self._parent.smallest_timeframe
            min_tf = self._parent._timeframes[min_tf_name]
            smart_bar = min_tf.open[self._smart_bar_slice][0]
        return np.r_[dataset[self._slice], smart_bar]

    @property
    def high(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="high",
        )
        smart_bar = np.array([])
        if not self.is_smallest_timeframe:
            min_tf_name = self._parent.smallest_timeframe
            min_tf = self._parent._timeframes[min_tf_name]
            smart_bar = min_tf.high[self._smart_bar_slice].max()
        return np.r_[dataset[self._slice], smart_bar]

    @property
    def low(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="low",
        )
        smart_bar = np.array([])
        if not self.is_smallest_timeframe:
            min_tf_name = self._parent.smallest_timeframe
            min_tf = self._parent._timeframes[min_tf_name]
            smart_bar = min_tf.low[self._smart_bar_slice].min()
        return np.r_[dataset[self._slice], smart_bar]

    @property
    def close(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="close",
        )
        smart_bar = np.array([])
        if not self.is_smallest_timeframe:
            min_tf_name = self._parent.smallest_timeframe
            min_tf = self._parent._timeframes[min_tf_name]
            smart_bar = min_tf.close[self._smart_bar_slice][-1]
        return np.r_[dataset[self._slice], smart_bar]

    @property
    def volume(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="tickvol",
        )
        smart_bar = np.array([])
        if not self.is_smallest_timeframe:
            min_tf_name = self._parent.smallest_timeframe
            min_tf = self._parent._timeframes[min_tf_name]
            smart_bar = min_tf.volume[self._smart_bar_slice].sum()
        return np.r_[dataset[self._slice], smart_bar]

    @property
    def datetime(self):
        dataset = self._data_source.retrieve_dataset(
            symbol=self.symbol,
            timeframe=self.name,
            dataset="timestamp",
        )
        smart_bar = np.array([])
        if not self.is_smallest_timeframe:
            min_tf_name = self._parent.smallest_timeframe
            min_tf = self._parent._timeframes[min_tf_name]
            smart_bar = min_tf.datetime[self._smart_bar_slice][-1]
        return np.r_[dataset[self._slice], smart_bar]


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

    def _initialize_parent_datetime_boundaries(self):
        min_dt = pd.to_datetime("1700")
        max_dt = pd.to_datetime("today")
        for name in self.timeframes:
            dt_low = self._timeframes[name]._all_datetimes.min()
            dt_high = self._timeframes[name]._all_datetimes.max()
            if dt_low > min_dt:
                min_dt = dt_low
            if dt_high < max_dt:
                max_dt = dt_high
        if min_dt > self._parent.start_datetime:
            print(
                f"Based on available data, start datetime has been modified to the following:"
            )
            print(f"start_datetime: {min_dt}")
            self._parent.start_datetime = min_dt
        if max_dt < self._parent.stop_datetime:
            print(
                f"Based on available data, stop datetime have been modified to the following:"
            )
            print(f"stop_datetime: {max_dt}")
            self._parent.stop_datetime = max_dt
        if min_dt > self._parent._min_datetime:
            self._parent._min_datetime = min_dt
        if max_dt < self._parent._max_datetime:
            self._parent._max_datetime = max_dt

    @property
    def smallest_timeframe(self):
        return min(self._timeframes, key=self._timeframes.get)

    @property
    def largest_timeframe(self):
        return max(self._timeframes, key=self._timeframes.get)

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
                if getattr(self, attr, False) and propogate:
                    setattr(self, attr, value)
                    self.update_timeframes(args=args, propogate=True)
                elif getattr(self, attr, False):
                    setattr(self, attr, value)
                elif propogate:
                    self.update_timeframes(args=args, propogate=True)
                else:
                    raise ValueError(
                        "args must be attribute of this Instrument object or its child Timeframes"
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
        for name in self.timeframes:
            self._timeframes[name]._update_smart_bar_slice()
        self._initialize_parent_datetime_boundaries()

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
