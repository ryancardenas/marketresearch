#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: backtest
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/14/2022

Code for backtesting strategies using data in fx_data.hdf5.
"""
from __future__ import annotations

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
    ):
        self.entry = entry
        self.stop = stop
        self.target = target
        self.volume = volume
        self.time_placed = time_placed
        self.position = "bull" if entry > stop else "bear"
        self.status = "placed"
        self.exit_fill = None
        self.exit_time = None
        self.entry_fill = None
        self.entry_time = None

    def update(self, data: pd.Series):
        assert (
            data["datetime"] > self.time_placed
        ), "update(timestamp) must be called after the time this trade was placed"
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
            if self.entry > self.stop:
                if data["open"] <= self.stop:
                    self.exit_fill = self.stop
                elif data["open"] >= self.target:
                    self.exit_fill = self.target
                elif data["low"] <= self.stop:
                    self.exit_fill = self.stop
                elif data["high"] >= self.target:
                    self.exit_fill = self.target
            elif self.entry < self.stop:
                if data["open"] >= self.stop:
                    self.exit_fill = self.stop
                elif data["open"] <= self.target:
                    self.exit_fill = self.target
                elif data["high"] >= self.stop:
                    self.exit_fill = self.stop
                elif data["low"] <= self.target:
                    self.exit_fill = self.target
            if self.exit_fill is not None:
                self.status = "completed"
                self.exit_time = data["datetime"]


class TradeLogic:
    """A container for trade logic."""

    def __init__(self, parent: BacktestAgent):
        self.parent = parent
        self.parent.trade_logic = self
        self.trade_cooldown = None
        self.last_trade_time = pd.Timestamp("1800")
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
        self.active_dataset = None
        self.datetime = None
        self.placed_trades = []
        self.active_trades = []
        self.completed_trades = []
        self.trade_logic = None
        self.current_set_name = None

    def data(self, timeframe):
        t0, tf = self.datasets[self.current_set_name]
        df = self._data[timeframe]
        return df[(df["datetime"] < tf) & (df["datetime"] < self.datetime)]

    def begin_backtest(self, dataset: str):
        self.current_set_name = dataset
        self.active_dataset = self.datasets[dataset]
        self.datetime = self.active_dataset[0]
        while self.datetime < self.active_dataset[-1]:
            self.trade_logic.execute_trade_logic()
            self.process_placed_trades()
            self.process_active_trades()
            self.step_forward()

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

    def process_placed_trades(self):
        bar = self._data[self.periods[0]].iloc[-1]
        for trade in self.placed_trades:
            if trade.status == "placed":
                trade.update(bar)

        placed = [t for t in self.placed_trades if t.status == "placed"]
        active = [t for t in self.placed_trades if t.status == "active"]
        self.placed_trades = placed
        self.active_trades = self.active_trades + active

    def process_active_trades(self):
        bar = self._data[self.periods[0]].iloc[-1]
        for trade in self.active_trades:
            if trade.status == "active":
                trade.update(bar)

        active = [t for t in self.placed_trades if t.status == "active"]
        completed = [t for t in self.placed_trades if t.status == "completed"]
        self.active_trades = active
        self.completed_trades = self.completed_trades + completed
