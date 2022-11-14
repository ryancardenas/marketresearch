#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: backtest
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/14/2022

Code for backtesting strategies using data in fx_data.hdf5.
"""

from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_datetime_bounds(data, periods):
    first_idx = data[periods[0]].apply(pd.Series.first_valid_index).max()
    first_dt = data[periods[0]]['datetime'].iloc[first_idx]
    last_idx = data[periods[0]].apply(pd.Series.last_valid_index).min()
    last_dt = data[periods[0]]['datetime'].iloc[last_idx]
    return first_dt, last_dt


class BacktestAgent:
    """An Agent used for backtesting trade strategies. Keeps an internal record of trades placed/active/completed
    and iterates through market data in small steps."""

    def __init__(self, data: dict, sorted_periods: list, train_ratio: float, num_validation_sets: int):
        self.data = data
        self.periods = sorted_periods
        self.train_ratio = train_ratio
        self.num_validation_sets = num_validation_sets
        self.start_datetime, self.stop_datetime = get_datetime_bounds(data, sorted_periods)
        self.datasets = self.get_datasets()

    def get_datasets(self):
        a = self.start_datetime
        b = self.stop_datetime
        end_test = a + (b - a) * self.train_ratio
        dt = (b - end_test) / self.num_validation_sets
        datasets = {
            'train': (a, end_test),
        }
        for n in range(self.num_validation_sets):
            datasets[f'val{n}'] = (end_test + n * dt, end_test + (n + 1) * dt)
        return datasets
