#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: indicators
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/8/2022

Indicator classes that compute signals for a given Timeframe.
"""

import numpy as np

import marketresearch.abstractions.abstractions as abmr


class SMA(abmr.AbstractIndicator):
    """A Simple Moving Average indicator. Computes average price over the last N bars."""

    def __init__(
        self, name: str, parent: abmr.AbstractTimeframe, n: int, method: str = "close"
    ):
        super().__init__(name=name, parent=parent)
        self.n = n
        self.method = method

    @property
    def values(self):
        return np.array(self._values)

    def update(self):
        """Updates the Indicator, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        x = np.mean(self._parent[self.method][-self.n :])
        self._values.append(x)
