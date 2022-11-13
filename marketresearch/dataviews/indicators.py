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


class SMA(abmr.AbstractIndicator):
    """A Simple Moving Average indicator. Computes average price over the last N bars."""

    def __init__(
        self, name: str, parent: abmr.AbstractTimeframe, n: int, dataset: str = "close"
    ):
        super().__init__(name=name, parent=parent)
        self.n = n
        self.dataset = dataset

    @property
    def values(self):
        return np.array(self._values)

    def compute(self):
        """Updates the Indicator, either by assimilating new market data or by incrementing the time step used for
        accessing data from a DataBase."""
        dataset = self._parent[self.dataset]
        if dataset.shape[0] < self.n:
            x = np.nan
        else:
            x = np.mean(dataset[-self.n :])
        self._values.append(x)

    def update(self, args: Optional[dict] = None):
        if args is None:
            args = {}
        for attr, value in args.items():
            if not isinstance(attr, str):
                raise ValueError(
                    "attr must be a string representing an attribute of this object"
                )
            else:
                setattr(self, attr, value)
        self._data_source.update()
