#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: timeframes
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/8/2022

Timeframe classes that wrap data typically charted for a financial instrument.
"""

from typing import List, Optional

import pandas as pd

import marketresearch.abstractions.abstractions as abmr


class FxTimeframe(abmr.AbstractTimeframe):
    """A Timeframe object for foreign exchange currency pairs, which have more attributes than an AbstractTimeframe."""

    def __init__(
        self,
        name: str,
        parent: abmr.AbstractInstrument,
        data_source: Optional[abmr.AbstractDataBase] = None,
    ):
        super().__init__(name=name, parent=parent, data_source=data_source)
        self._connect_to_database()
        self.symbol = self._parent.name

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

    def update(self, attrs: Optional[List] = None, values: Optional[List] = None):
        if attrs is None:
            attrs = []
        if values is None:
            values = []
        assert len(attrs) == len(values), "attrs and values must have same length"
        for attr, value in zip(attrs, values):
            if attr is None:
                raise ValueError("attr must not be None")
            else:
                setattr(self, attr, value)
        self._data_source.update()

    def _connect_to_database(self):
        self._data_source.connect()
