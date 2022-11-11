#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: datafeeds
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/8/2022

DataFeed classes that can be connected to a DataView.
"""

from typing import List, Optional

import pandas as pd

import marketresearch.abstractions.abstractions as abmr
import marketresearch.dataviews.timeframes as tf


class FxInstrument(abmr.AbstractInstrument):
    """An Instrument object for foreign exchange currency pairs."""

    def __init__(self, name: str, data_source: abmr.AbstractDataBase):
        super().__init__(name=name, data_source=data_source)
        self._timeframes = {}
        self._default_timeframe_class = tf.FxTimeframe

    def add_timeframe(self, timeframes: dict):
        """Creates Timeframe objects with their respective data sources and links them to this object, provided they
        don't already exist and are not duplicates of each other."""
        for name, args in timeframes.items():
            if name in self.timeframes:
                print(f"DataFeed with name {name} is already linked! Skipping...")
            else:
                timeframe = self._default_timeframe_class(
                    name=name, parent=self, **args
                )
                self._timeframes[name] = timeframe

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
