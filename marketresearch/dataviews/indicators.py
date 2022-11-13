#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: indicators
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/8/2022

Indicator classes that compute signals for a given Timeframe.
"""

from typing import Optional

import numpy as np

import marketresearch.abstractions.abstractions as abmr
import marketresearch.dataviews.backtesting as bt


class SMA(bt.AbstractIndicator):
    """A Simple Moving Average indicator. Computes average price over the last N bars."""

    def __init__(
        self,
        name: str,
        parent: bt.BacktestTimeframe,
        n: int,
        dataset_name: str = "close",
    ):
        super().__init__(name=name, parent=parent, dataset_name=dataset_name)
        self.n = n
        self._init_compute()

    @property
    def values(self):
        return np.array(self._values)

    def _init_compute(self):
        """Updates the Indicator, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        dataset = self._parent[self.dataset_name]
        vals = np.full(shape=dataset.shape[0], fill_value=np.nan)
        vals[8:] = np.convolve(dataset, np.ones(9) / 9, "valid")
        self._values = list(vals)

    def update(self):
        dataset = self._parent[self.dataset_name]
        if len(self._values) < self.n:
            x = np.nan
        else:
            x = np.mean(dataset[-self.n :])
        self._values.append(x)
