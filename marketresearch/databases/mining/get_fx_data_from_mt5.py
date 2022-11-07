#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: get_fx_data_from_mt5
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/5/2022

This code downloads candlestick data from MetaTrader5 and stores the data to disk in an HDF5 file. The general structure
for the stored data is:

HDF5_FILE/
    FX_PAIR_1/
        TIMEFRAME_1/
            DATE
            OPEN
            HIGH
            LOW
            CLOSE
            TICKVOLUME
            VOLUME
        TIMEFRAME_2/...
    FX_PAIR_2/
        TIMEFRAME_1/...
    FX_PAIR_3/...

ToDo: Refactor functions into Agent/Client/DataView/Database structure defined in README.md.
"""

import glob
import os
import pytest
import time

import h5py
import MetaTrader5 as mt5
import numpy as np
import pandas as pd

import marketresearch.clients.mt5.data_enums as fxde
from marketresearch.clients.secrets import MT5_ACCT_INFO

ACCT_INFO = MT5_ACCT_INFO
AVAILABLE_FREQUENCIES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "Daily": mt5.TIMEFRAME_D1,
    "Weekly": mt5.TIMEFRAME_W1,
    "Monthly": mt5.TIMEFRAME_MN1,
}


def read_csv_to_dataframe(fn):
    df = pd.read_csv(
        fn,
        delimiter=",",
        encoding="utf-16",
        names=["date", "open", "high", "low", "close", "tickvol", "volume"],
        usecols=["date", "open", "high", "low", "close", "tickvol"],
        dtype={
            "date": str,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "tickvol": np.int64,
            "volume": int,
        },
        parse_dates=["date"],
    )
    df["timestamp"] = df["date"].view("int64")
    df.set_index("date", inplace=True)
    os.unlink(fn)
    return df


def create_timeframe_group(symbol_group, tf, df):
    grp = symbol_group.require_group(tf)
    for name in ["timestamp", "open", "high", "low", "close", "tickvol"]:
        x = df[name].values
        if name in grp:
            dset = grp[name]
            dset.resize(x.shape[0], axis=0)
            dset[:] = x
        else:
            dset = grp.create_dataset(
                name,
                data=x,
                shape=x.shape,
                dtype=x.dtype,
                maxshape=(None,),
                compression="gzip",
            )


def read_datasets_to_dataframe(timeframe_group):
    data = {}
    for name in ["timestamp", "open", "high", "low", "close", "tickvol"]:
        data[name] = timeframe_group[name][:]
    df2 = pd.DataFrame(data)
    df2["date"] = pd.to_datetime(df2["timestamp"]).values
    df2.set_index("date", inplace=True)
    return df2


def append_new_values(df, df2):
    df = df.combine_first(df2).sort_index()
    for col in df.columns:
        df[col] = df[col].astype(df2[col].dtype)
    return df


def overwrite_timeframe_data(grp, df):
    for name in ["timestamp", "open", "high", "low", "close", "tickvol"]:
        x = df[name].values
        dset = grp[name]
        dset.resize(x.shape[0], axis=0)
        dset[:] = x


def retrieve_data_from_mt5_server(sym, tf_obj, nbars=50000, num_retries=5):
    retry_wait_seconds = 3
    tries = 0
    df = pd.DataFrame()
    while tries <= num_retries:
        connection_established = mt5.initialize(**ACCT_INFO)
        if connection_established:
            rates = mt5.copy_rates_from_pos(sym, tf_obj, 0, nbars)
            df = pd.DataFrame(rates)
            if df.shape[0] > 0:
                break
            else:
                tries += 1
                time.sleep(retry_wait_seconds)
        else:
            print(
                f"Connection not established. Retrying in {retry_wait_seconds} seconds..."
            )
            tries += 1
            time.sleep(retry_wait_seconds)

    if tries > num_retries:
        raise ConnectionError("Could not connect to MT5 terminal.")

    df["date"] = pd.to_datetime(df["time"], unit="s")
    df["timestamp"] = df["date"].view("int64")
    df.set_index("date", inplace=True)
    df.rename(columns={"tick_volume": "tickvol"}, inplace=True)
    df = df[["timestamp", "open", "high", "low", "close", "tickvol"]]

    mt5.shutdown()
    return df


def update_hdf5(f, symbol, tf, df):
    sym = f.require_group(symbol)
    if tf not in sym:
        create_timeframe_group(sym, tf, df)
    else:
        grp = sym[tf]
        df2 = read_datasets_to_dataframe(grp)
        df = append_new_values(df, df2)
        overwrite_timeframe_data(grp, df)


def archive_data_from_csv(srcdir, trg):
    flist = glob.glob(str(srcdir) + "/**/*.csv", recursive=True)
    with h5py.File(trg, "a") as f:
        for fn in flist:
            fbase = os.path.basename(fn)
            symbol = fbase[:6]
            tf = fbase[6:-4]
            df = read_csv_to_dataframe(fn)
            update_hdf5(f, symbol, tf, df)

    return True


def archive_data_from_mt5(trg, symbols, frequencies="all", nbars=50000):
    if frequencies == "all":
        timeframes = AVAILABLE_FREQUENCIES
    elif isinstance(frequencies, list):
        timeframes = {
            key: val for key, val in AVAILABLE_FREQUENCIES.items() if key in frequencies
        }
    else:
        raise ValueError(
            "Argument 'frequencies' must be either 'all' or a list of strings."
        )

    with h5py.File(trg, "a") as f:
        for symbol in symbols:
            for tf, tf_obj in timeframes.items():
                print(f"\nRetrieving {symbol}.{tf} data...")
                df = retrieve_data_from_mt5_server(symbol, tf_obj, nbars=nbars)
                print("Updating hdf5 file...")
                update_hdf5(f, symbol, tf, df)
                print("Data stored!")

    return True


def get_deals(start_date="01-01-2020", end_date="today"):
    start_date = pd.to_datetime(start_date).timestamp()
    end_date = pd.to_datetime(end_date).timestamp()

    mt5.initialize(**ACCT_INFO)
    deals = mt5.history_deals_get(start_date, end_date)

    data = []
    for deal in deals:
        vals = {
            "ticket_id": deal.ticket,
            "order": deal.order,
            "time": pd.to_datetime(deal.time, unit="s"),
            "type": fxde.ENUM_DEAL_TYPE(deal.type).name,
            "entry": fxde.ENUM_DEAL_ENTRY(deal.entry).name,
            "position_id": deal.position_id,
            "reason": fxde.ENUM_DEAL_REASON(deal.reason).name,
            "volume": deal.volume,
            "price": deal.price,
            "commission": deal.commission,
            "swap": deal.swap,
            "profit": deal.profit,
            "fee": deal.fee,
            "symbol": deal.symbol,
            "comment": deal.comment,
            "magic_id": deal.magic,
            "external_id": deal.external_id,
        }
        data.append(vals)

    df = pd.DataFrame(data)
    deals = df[df["position_id"] != 0]
    deals.set_index(["position_id", "ticket_id"], inplace=True)
    return deals


def get_orders(start_date="01-01-2020", end_date="today"):
    start_date = pd.to_datetime(start_date).timestamp()
    end_date = pd.to_datetime(end_date).timestamp()
    mt5.initialize(**ACCT_INFO)
    orders = mt5.history_orders_get(start_date, end_date)

    data = []
    for order in orders:
        vals = {
            "ticket_id": order.ticket,
            "time_setup": pd.to_datetime(order.time_setup, unit="s"),
            "time_done": pd.to_datetime(order.time_done, unit="s"),
            "order_type": fxde.ENUM_ORDER_TYPE(order.type).name,
            "time_type": fxde.ENUM_ORDER_TYPE_TIME(order.type_time).name,
            "fill_type": fxde.ENUM_ORDER_TYPE_FILLING(order.type_filling).name,
            "state": fxde.ENUM_ORDER_STATE(order.state).name,
            "position_id": order.position_id,
            "reason": fxde.ENUM_ORDER_REASON(order.reason).name,
            "volume_initial": order.volume_initial,
            "volume_current": order.volume_current,
            "price_open": order.price_open,
            "sl": order.sl,
            "tp": order.tp,
            "price_current": order.price_current,
            "price_stoplimit": order.price_stoplimit,
            "symbol": order.symbol,
            "comment": order.comment,
            "external_id": order.external_id,
            "magic_id": order.magic,
        }
        data.append(vals)

    df = pd.DataFrame(data)
    orders = df[df["position_id"] != 0]
    orders.set_index(["position_id", "ticket_id"], inplace=True)
    return orders


if __name__ == "__main__":
    from marketresearch.utils import PROJECT_ROOT_DIRECTORY

    tries = 0
    pytest_retries = 3
    rtdir = PROJECT_ROOT_DIRECTORY / "marketresearch\\databases\\"
    trg = rtdir / "fx_data.hdf5"
    symbols = ["EURUSD", "USDJPY", "USDCAD", "GBPUSD", "NZDUSD", "AUDUSD", "USDCHF"]

    with open("fx_data_mining.log", "a") as f:
        now = pd.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{now} -- Running pytests...\n")
        exit_code = pytest.main()

        now = pd.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{now} -- Testing returned exit code: {exit_code}\n")

        if exit_code != 0:
            while tries <= pytest_retries and exit_code != 0:
                now = pd.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{now} -- Retrying pytests...\n")
                pytest_retries = 3
                exit_code = pytest.main()

                now = pd.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{now} -- Testing returned exit code: {exit_code}\n")

        if tries > pytest_retries:
            f.write(f"{now} -- Pytest failed. Aborting.\n")
        else:
            now = pd.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{now} -- Storing data...\n")
            successful_run = archive_data_from_mt5(trg, symbols)

            now = pd.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            if successful_run:
                f.write(f"{now} -- Data successfully stored!\n")
            else:
                f.write(
                    f"{now} -- ERROR: Process failed to run fx_data.archive_data_from_mt5()\n"
                )
