#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: backtest
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/14/2022

Code for backtesting strategies using data in fx_data.hdf5.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd


def get_datetime_bounds(data, periods):
    first_idx = data[periods[0]].apply(pd.Series.first_valid_index).max()
    first_dt = data[periods[0]]["datetime"].iloc[first_idx]
    last_idx = data[periods[0]].apply(pd.Series.last_valid_index).min()
    last_dt = data[periods[0]]["datetime"].iloc[last_idx]
    return first_dt, last_dt


class BacktestTrade:
    """Class representing trades. Allows for keeping track of trades that have been placed, that are active,
    and that are completed."""

    def __init__(
        self,
        entry: float,
        stop: float,
        target: float,
        volume: int,
        time_placed: pd.Timestamp,
        trade_timeout: pd.Timedelta,
    ):
        self.entry = entry
        self.stop = stop
        self.target = target
        self.volume = volume
        self.time_placed = time_placed
        self.trade_timeout = time_placed + trade_timeout
        self.position = "bull" if entry > stop else "bear"
        self.status = "placed"
        self.exit_fill = None
        self.exit_time = None
        self.entry_fill = None
        self.entry_time = None
        self.is_win = None
        self.outcome_r = None
        self.outcome_amount = None

    def update(self, data: pd.Series):
        # assert (
        #     data["datetime"] >= self.time_placed
        # ), "update(timestamp) must be called at or after the time this trade was placed"
        if self.status == "placed":
            if self.entry > self.stop:
                if data["high"] >= self.entry:
                    self.entry_fill = self.entry
            elif self.entry < self.stop:
                if data["low"] <= self.entry:
                    self.entry_fill = self.entry
            if self.entry_fill is not None:
                self.status = "active"
                self.entry_time = data["datetime"]

        if self.status == "active":
            if self.entry > self.stop:  # bullish
                if data["open"] <= self.stop:
                    self.exit_fill = self.stop
                    self.is_win = 0
                elif data["open"] >= self.target:
                    self.exit_fill = self.target
                    self.is_win = 1
                elif data["low"] <= self.stop:
                    self.exit_fill = self.stop
                    self.is_win = 0
                elif data["high"] >= self.target:
                    self.exit_fill = self.target
                    self.is_win = 1
            elif self.entry < self.stop:  # bearish
                if data["open"] >= self.stop:
                    self.exit_fill = self.stop
                    self.is_win = 0
                elif data["open"] <= self.target:
                    self.exit_fill = self.target
                    self.is_win = 1
                elif data["high"] >= self.stop:
                    self.exit_fill = self.stop
                    self.is_win = 0
                elif data["low"] <= self.target:
                    self.exit_fill = self.target
                    self.is_win = 1
            if self.exit_fill is not None:
                self.status = "completed"
                self.exit_time = data["datetime"]
                risk = abs(self.entry - self.stop)
                win = self.is_win * abs(self.target - self.entry)
                loss = (1 - self.is_win) * risk
                self.outcome_amount = win - loss
                self.outcome_r = self.outcome_amount / risk


class TradeLogic:
    """A container for trade logic."""

    def __init__(self, parent: BacktestAgent):
        self.parent = parent
        self.parent.trade_logic = self
        self.trade_cooldown = None
        self.position = None
        self.volume = 0

    def execute_trade_logic(self):
        pass


class BacktestAgent:
    """An Agent used for backtesting trade strategies. Keeps an internal record of trades placed/active/completed
    and iterates through market data in small steps."""

    def __init__(
        self,
        data: dict,
        sorted_periods: list,
        train_ratio: float,
        num_validation_sets: int,
    ):
        self._data = data
        self.periods = sorted_periods
        self.train_ratio = train_ratio
        self.num_validation_sets = num_validation_sets
        self.start_datetime, self.stop_datetime = get_datetime_bounds(
            data, sorted_periods
        )
        self.datasets = self.get_datasets()
        self.timestep = self.get_timestep()
        self.active_dataset_datetime_boundaries = None
        self.datetime = None
        self.last_trade_time = pd.Timestamp("1800")
        self.placed_trades = []
        self.active_trades = []
        self.completed_trades = []
        self.trade_logic = None
        self.current_set_name = None
        self._slices = {}

    def data(self, period):
        slc = self._slices[period]
        return self._data[period].iloc[slc]

    def init_slices(self):
        t0, tf = self.datasets[self.current_set_name]
        for period in self.periods:
            df = self._data[period]
            stop = df[(df["datetime"] < tf) & (df["datetime"] < self.datetime)].index[
                -1
            ]
            self._slices[period] = slice(0, stop)

    def begin_backtest(
        self, dataset: str, display_delta: pd.Timedelta = pd.Timedelta("1day")
    ):
        print(f"BEGINNING BACKTEST FOR DATASET: {dataset}")
        self.current_set_name = dataset
        self.active_dataset_datetime_boundaries = self.datasets[dataset]
        self.datetime = self.active_dataset_datetime_boundaries[0]
        self.init_slices()
        previous = self.datetime
        start_time = time.time()
        while self.datetime < self.active_dataset_datetime_boundaries[-1]:
            self.trade_logic.execute_trade_logic()
            self.process_placed_trades()
            self.process_active_trades()
            self.step_forward()
            if self.datetime >= previous + display_delta:
                self.display_backtest_progress(start_time=start_time)
                previous = self.datetime
                start_time = time.time()
        print(f"BACKTESTING COMPLETE FOR DATASET: {dataset}")

    def display_backtest_progress(self, start_time):
        stop_time = time.time()
        nplaced = len(self.placed_trades)
        na = len(self.active_trades)
        nc = len(self.completed_trades)
        print(
            f"Backtested up to {self.datetime} / {self.active_dataset_datetime_boundaries[-1]}"
            f"    placed:{nplaced + na + nc}  active:{na}  completed:{nc}    ({stop_time - start_time:.2f} [s])"
        )

    def get_datasets(self):
        a = self.start_datetime
        b = self.stop_datetime
        end_test = a + (b - a) * self.train_ratio
        dt = (b - end_test) / self.num_validation_sets
        datasets = {
            "train": (a, end_test),
        }
        for n in range(self.num_validation_sets):
            datasets[f"val{n}"] = (end_test + n * dt, end_test + (n + 1) * dt)
        return datasets

    def get_timestep(self):
        datetimes = self._data[self.periods[0]]["datetime"]
        return datetimes.diff().min()

    def step_forward(self):
        self.datetime += self.timestep
        for period in self.periods:
            df = self._data[period]
            slc = self._slices[period]
            new_stop = slc.stop + 1
            if df.iloc[new_stop]["datetime"] < self.datetime:
                self._slices[period] = slice(0, new_stop)

    def process_placed_trades(self):
        bar = self.data(self.periods[0]).iloc[-1]
        pop_nums = []
        for i, trade in enumerate(self.placed_trades):
            if bar["datetime"] >= trade.trade_timeout:
                pop_nums.append(i)
            elif trade.status == "placed":
                trade.update(bar)

        for i in sorted(pop_nums, reverse=True):
            self.placed_trades.pop(i)

        placed = [t for t in self.placed_trades if t.status == "placed"]
        active = [t for t in self.placed_trades if t.status == "active"]
        self.placed_trades = placed
        self.active_trades = self.active_trades + active

    def process_active_trades(self):
        bar = self.data(self.periods[0]).iloc[-1]
        for trade in self.active_trades:
            if trade.status == "active":
                trade.update(bar)

        active = [t for t in self.active_trades if t.status == "active"]
        completed = [t for t in self.active_trades if t.status == "completed"]
        self.active_trades = active
        self.completed_trades = self.completed_trades + completed
