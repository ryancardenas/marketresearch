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

    def __init__(
        self,
        name: str,
        parent: abmr.AbstractDataView,
        data_source: abmr.AbstractDataBase,
    ):
        super().__init__(name=name, parent=parent, data_source=data_source)
        self._timeframes = {}
        self._default_timeframe_class = tf.FxTimeframe
