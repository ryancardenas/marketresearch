#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: indicators
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/14/2022

Functions for computing indicators.
"""

from pathlib import Path

import numpy as np
import pandas as pd


def window_sum(x, w):
    c = np.cumsum(x)
    s = c[w - 1 :]
    s[1:] -= c[:-w]
    return s


def window_lin_reg(x, y, w):
    sx = window_sum(x, w)
    sy = window_sum(y, w)
    sx2 = window_sum(x**2, w)
    sxy = window_sum(x * y, w)
    slope = (w * sxy - sx * sy) / (w * sx2 - sx**2)
    intercept = (sy - slope * sx) / w
    return slope, intercept


def SMA(df, n, method="close", include_slope=False, slope_n=4):
    dataset = df[method].values
    vals = np.full(shape=dataset.shape[0], fill_value=np.nan)
    vals[n - 1 :] = np.convolve(dataset, np.ones(n) / n, "valid")
    if include_slope:
        slopes = np.full(shape=dataset.shape[0], fill_value=np.nan)
        x = np.arange(dataset.shape[0])
        fit = window_lin_reg(x[n - 1 :], vals[n - 1 :], slope_n)
        slopes[n - 2 + slope_n :] = fit[0]
        return pd.DataFrame({f"val": vals, f"slope": slopes})
    else:
        return vals


def BollingerBand(df, sigma, n=20):
    tp = (df["high"] + df["low"] + df["close"]) / 3
    std = tp.rolling(n).std()
    ma = np.full(shape=tp.shape[0], fill_value=np.nan)
    ma[n - 1 :] = np.convolve(tp, np.ones(n) / n, "valid")
    return ma + sigma * std


def HeikenAshi(df):
    cl = (df["open"] + df["high"] + df["low"] + df["close"]).iloc[1:].values / 4
    op = (df["open"] + df["close"]).iloc[:-1].values / 2
    hi = df[["high", "open", "close"]].iloc[1:].max(axis=1).values
    lo = df[["low", "open", "close"]].iloc[1:].min(axis=1).values
    ha = pd.DataFrame({"open": op, "high": hi, "low": lo, "close": cl})
    first_row = pd.DataFrame(
        np.full(shape=(1, 4), fill_value=np.nan),
        columns=["open", "high", "low", "close"],
    )
    return pd.concat([first_row, ha])
