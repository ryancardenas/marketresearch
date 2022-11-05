#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: test_get_fx_data_from_mt5
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/5/2022

Put docstring here.
"""

import csv
import glob
import pytest

import h5py
import MetaTrader5 as mt5
import numpy as np
import pandas as pd

import marketresearch.data.mining.get_fx_data_from_mt5 as fxd
from marketresearch.utils import PROJECT_ROOT_DIRECTORY

TESTDIR = PROJECT_ROOT_DIRECTORY / "marketresearch\\data\\mining\\tests\\"


class Test_read_csv_to_dataframe:
    """Tests that read_csv_to_dataframe() meets the following expectations:
    - Output contains all data from all columns.
    - Output dtypes are correct for all columns.
    - Output timestamps are equal to timestamp typecasts of index column.
    - Output timestamps are strictly increasing.
    """

    @pytest.fixture(scope="function")
    def tmp_data(self, tmpdir):
        n = 1000
        rt = tmpdir.mkdir("data")
        fn = rt.join("tmp_data.csv")

        timestamp = (
            (np.random.choice(1000000, n, replace=False) + 16000000) * 1e11
        ).astype("int64")
        timestamp.sort()
        date = pd.to_datetime(timestamp).strftime("%Y.%m.%d %H:%M")
        timestamp = pd.to_datetime(date).view("int64")
        op = np.random.random(size=n) + 0.5
        hi = np.random.random(size=n) + 0.5
        lo = np.random.random(size=n) + 0.5
        cl = np.random.random(size=n) + 0.5
        tickvol = np.random.randint(low=0, high=200, size=n).astype("int64")
        vol = np.zeros_like(op, dtype=int)
        test_data = np.vstack([op, hi, lo, cl, tickvol, timestamp]).T

        with open(fn, mode="w", newline="", encoding="utf-16") as f:
            fw = csv.writer(f)
            fw.writerows(zip(date, op, hi, lo, cl, tickvol, vol))

        return fn, test_data

    def test_output_contains_all_data_from_all_columns(self, tmp_data):
        fn, test_data = tmp_data
        df = fxd.read_csv_to_dataframe(fn)
        cols = ["open", "high", "low", "close", "tickvol", "timestamp"]
        assert np.allclose(df[cols].values, test_data)

    def test_dtypes_all_correct(self, tmp_data):
        fn, test_data = tmp_data
        df = fxd.read_csv_to_dataframe(fn)
        dtypes = {
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "tickvol": np.int64,
            "timestamp": np.int64,
        }
        for key, dtype in dtypes.items():
            assert df[key].dtype == dtype

    def test_timestamps_equal_to_datetime_typecasts_of_index(self, tmp_data):
        fn, test_data = tmp_data
        df = fxd.read_csv_to_dataframe(fn)
        assert np.array_equal(df.index.view(np.int64), df["timestamp"].values)

    def test_output_timestamps_strictly_increasing(self, tmp_data):
        fn, test_data = tmp_data
        df = fxd.read_csv_to_dataframe(fn)
        assert np.all(np.diff(df["timestamp"].values) > 0)


class Test_create_timeframe_group:
    """Tests that create_timeframe_group() meets the following expectations:
    - After call, hdf5 has group with name specified by tf.
    - After call, all datasets in group have same length as df.
    - After call, all datasets in group have same dtype as respective df column.
    """

    @pytest.fixture(scope="function")
    def tmp_data(self, tmpdir):
        n = 1000
        rt = tmpdir.mkdir("data")
        fn = rt.join("tmp_trg.hdf5")

        timestamp = (
            (np.random.choice(10000000, n, replace=False) + 160000000) * 1e10
        ).astype("int64")
        timestamp.sort()
        date = pd.to_datetime(timestamp).strftime("%Y.%m.%d %H:%M")
        op = np.random.random(size=n) + 0.5
        hi = np.random.random(size=n) + 0.5
        lo = np.random.random(size=n) + 0.5
        cl = np.random.random(size=n) + 0.5
        tickvol = np.random.randint(low=0, high=200, size=n).astype("int64")
        vol = np.zeros_like(op, dtype=int)
        test_data = pd.DataFrame(
            data={
                "open": op,
                "high": hi,
                "low": lo,
                "close": cl,
                "tickvol": tickvol,
                "timestamp": timestamp,
            }
        )

        return fn, test_data

    @pytest.mark.parametrize(
        "sym, tf",
        [["EURUSD", "M1"], ["AUDEUR", "M15"], ["ABCDFG", "H4"], ["123456", "D1"]],
    )
    def test_group_name_is_specified_by_tf(self, tmp_data, sym, tf):
        fn, df = tmp_data
        with h5py.File(fn, "w") as f:
            symbol_group = f.create_group(sym)
            fxd.create_timeframe_group(symbol_group, tf, df)

            assert tf in symbol_group

    @pytest.mark.parametrize(
        "sym, tf",
        [["EURUSD", "M1"], ["AUDEUR", "M15"], ["ABCDFG", "H4"], ["123456", "D1"]],
    )
    def test_datasets_have_same_length_as_original_data(self, tmp_data, sym, tf):
        fn, df = tmp_data
        with h5py.File(fn, "w") as f:
            symbol_group = f.create_group(sym)
            fxd.create_timeframe_group(symbol_group, tf, df)

            for key in symbol_group[tf].keys():
                x = symbol_group[tf][key][:]
                assert x.shape == df[key].shape

    @pytest.mark.parametrize(
        "sym, tf",
        [["EURUSD", "M1"], ["AUDEUR", "M15"], ["ABCDFG", "H4"], ["123456", "D1"]],
    )
    def test_datasets_have_same_dtype_as_original_data(self, tmp_data, sym, tf):
        fn, df = tmp_data
        with h5py.File(fn, "w") as f:
            symbol_group = f.create_group(sym)
            fxd.create_timeframe_group(symbol_group, tf, df)

            for key in symbol_group[tf].keys():
                x = symbol_group[tf][key][:]
                assert x.dtype == df[key].dtype


class Test_read_datasets_to_dataframe:
    """Tests that read_datasets_to_dataframe() meets the following expectations:
    - Output contains exact same data as was stored to disk.
    """

    @pytest.fixture(scope="function")
    def tmp_data(self, tmpdir):
        n = 1000
        rt = tmpdir.mkdir("data")
        fn = rt.join("tmp_trg.hdf5")

        timestamp = (
            (np.random.choice(10000000, n, replace=False) + 160000000) * 1e10
        ).astype("int64")
        timestamp.sort()
        date = pd.to_datetime(timestamp).strftime("%Y.%m.%d %H:%M")
        op = np.random.random(size=n) + 0.5
        hi = np.random.random(size=n) + 0.5
        lo = np.random.random(size=n) + 0.5
        cl = np.random.random(size=n) + 0.5
        tickvol = np.random.randint(low=0, high=200, size=n).astype("int64")
        vol = np.zeros_like(op, dtype=int)
        data_dict = {
            "timestamp": timestamp,
            "open": op,
            "high": hi,
            "low": lo,
            "close": cl,
            "tickvol": tickvol,
        }
        test_data = pd.DataFrame(data=data_dict)

        with h5py.File(fn, "a") as f:
            for key, val in data_dict.items():
                f.create_dataset(key, data=val, dtype=val.dtype, shape=val.shape)

        return fn, test_data

    def test_output_contains_same_data_as_stored_to_disk(self, tmp_data):
        fn, df = tmp_data
        with h5py.File(fn, "a") as f:
            df2 = fxd.read_datasets_to_dataframe(f)
            assert np.array_equal(df.values, df2.values)


class Test_append_new_values:
    """Tests that append_new_values() meets the following expectations:
    - Given overlapping sections of the same dataframe, returns the entire dataframe without duplicates.
    """

    @pytest.fixture(scope="function")
    def tmp_data(self, tmpdir):
        n = 1000

        timestamp = (
            (np.random.choice(10000000, n, replace=False) + 160000000) * 1e10
        ).astype("int64")
        timestamp.sort()
        date = pd.to_datetime(timestamp).strftime("%Y.%m.%d %H:%M")
        op = np.random.random(size=n) + 0.5
        hi = np.random.random(size=n) + 0.5
        lo = np.random.random(size=n) + 0.5
        cl = np.random.random(size=n) + 0.5
        tickvol = np.random.randint(low=0, high=200, size=n).astype("int64")
        vol = np.zeros_like(op, dtype=int)
        data_dict = {
            "date": date,
            "timestamp": timestamp,
            "open": op,
            "high": hi,
            "low": lo,
            "close": cl,
            "tickvol": tickvol,
        }
        test_data = pd.DataFrame(data=data_dict)
        test_data.set_index("date")

        return test_data

    def test_output_contains_same_data_as_stored_to_disk(self, tmp_data):
        df = tmp_data
        N = df.shape[0]
        df_a = df.iloc[: 2 * N // 3]
        df_b = df.iloc[N // 3 :]
        df2 = fxd.append_new_values(df_a, df_b)
        assert df.equals(df2)


class Test_overwrite_timeframe_data:
    """Tests that overwrite_timeframe_data() meets the following expectations:
    - Successfully overwrites old data with newer, larger data.
    """

    @pytest.fixture(scope="function")
    def tmp_data(self, tmpdir):
        n = 1000
        rt = tmpdir.mkdir("data")
        fn = rt.join("tmp_trg.hdf5")

        timestamp = (
            (np.random.choice(10000000, n, replace=False) + 160000000) * 1e10
        ).astype("int64")
        timestamp.sort()
        date = pd.to_datetime(timestamp).strftime("%Y.%m.%d %H:%M")
        op = np.random.random(size=n) + 0.5
        hi = np.random.random(size=n) + 0.5
        lo = np.random.random(size=n) + 0.5
        cl = np.random.random(size=n) + 0.5
        tickvol = np.random.randint(low=0, high=200, size=n).astype("int64")
        vol = np.zeros_like(op, dtype=int)
        data_dict = {
            "open": op,
            "high": hi,
            "low": lo,
            "close": cl,
            "tickvol": tickvol,
            "timestamp": timestamp,
        }
        test_data = pd.DataFrame(data=data_dict)

        with h5py.File(fn, "a") as f:
            for key, val in data_dict.items():
                x = val[: n // 3]
                dset = f.create_dataset(
                    name=key,
                    data=x,
                    dtype=x.dtype,
                    shape=x.shape,
                    maxshape=(None,),
                    compression="gzip",
                )

        return fn, test_data

    def test_successfully_replaces_old_datasets_with_newer_larger_data(self, tmp_data):
        fn, df = tmp_data
        with h5py.File(fn, "a") as f:
            fxd.overwrite_timeframe_data(f, df)
            for col in df.columns:
                assert np.array_equal(f[col][:], df[col].values)


class Test_retrieve_data_from_mt5_server:
    """Tests that retrieve_data_from_mt5_server() meets the following expectations:
    - Successfully returns dataframe of expected length.
    """

    @pytest.mark.parametrize("tf, nbars", [("M1", 10), ("H4", 13), ("Daily", 7)])
    def test_returns_dataframe_of_expected_length(self, tf, nbars):
        sym = "EURUSD"
        df = fxd.retrieve_data_from_mt5_server(
            sym, fxd.AVAILABLE_FREQUENCIES[tf], nbars=nbars
        )
        assert df.shape[0] == nbars


class Test_archive_data_from_csv:
    """Tests that archive_data_from_csv() meets the following expectations:
    - Successfully creates new group with OHLCT data.
    - Successfully overwrites existing OHLCT data with newer, larger data.
    - Deletes source CSV files after run.
    """

    @pytest.fixture(scope="function")
    def tmp_data_csv_only(self, tmp_path):
        n = 1000
        num_src_files = 3
        grp_names = ["EURUSDM1", "JPYCADH4", "ABCXYZDaily"]
        rt = tmp_path / "data"
        rt.mkdir()

        test_data = {}
        for i in range(num_src_files):
            timestamp = (
                (np.random.choice(1000000, n, replace=False) + 16000000) * 1e11
            ).astype("int64")
            timestamp.sort()
            date = pd.to_datetime(timestamp).strftime("%Y.%m.%d %H:%M")
            timestamp = pd.to_datetime(date).view("int64")
            op = (np.random.random(size=n) + 0.5).round(5)
            hi = (np.random.random(size=n) + 0.5).round(5)
            lo = (np.random.random(size=n) + 0.5).round(5)
            cl = (np.random.random(size=n) + 0.5).round(5)
            tickvol = np.random.randint(low=0, high=200, size=n).astype("int64")
            vol = np.zeros_like(op, dtype=int)
            data_dict = {
                "date": date,
                "open": op,
                "high": hi,
                "low": lo,
                "close": cl,
                "tickvol": tickvol,
                "vol": vol,
                "timestamp": timestamp,
            }
            df = pd.DataFrame(data=data_dict)
            csv_cols = ["date", "open", "high", "low", "close", "tickvol", "vol"]
            df.to_csv(
                rt / f"{grp_names[i]}.csv",
                index=False,
                columns=csv_cols,
                encoding="utf-16",
                header=False,
            )

            hdf5_cols = ["timestamp", "open", "high", "low", "close", "tickvol"]
            test_data[grp_names[i]] = df[hdf5_cols]

        return rt, test_data

    @pytest.fixture(scope="function")
    def tmp_data_csv_and_hdf5(self, tmp_path):
        n = 1000
        num_src_files = 3
        grp_names = ["EURUSDM1", "JPYCADH4", "ABCXYZDaily"]
        rt = tmp_path / "data"
        rt.mkdir()
        fn = rt / "tmp_trg.hdf5"

        with h5py.File(fn, "a") as f:
            test_data = {}
            for i in range(num_src_files):
                timestamp = (
                    (np.random.choice(1000000, n, replace=False) + 16000000) * 1e11
                ).astype("int64")
                timestamp.sort()
                date = pd.to_datetime(timestamp).strftime("%Y.%m.%d %H:%M")
                timestamp = pd.to_datetime(date).view("int64")
                op = (np.random.random(size=n) + 0.5).round(5)
                hi = (np.random.random(size=n) + 0.5).round(5)
                lo = (np.random.random(size=n) + 0.5).round(5)
                cl = (np.random.random(size=n) + 0.5).round(5)
                tickvol = np.random.randint(low=0, high=200, size=n).astype("int64")
                vol = np.zeros_like(op, dtype=int)
                data_dict = {
                    "date": date,
                    "open": op,
                    "high": hi,
                    "low": lo,
                    "close": cl,
                    "tickvol": tickvol,
                    "vol": vol,
                    "timestamp": timestamp,
                }
                df = pd.DataFrame(data=data_dict)
                csv_cols = ["date", "open", "high", "low", "close", "tickvol", "vol"]
                df.to_csv(
                    rt / f"{grp_names[i]}.csv",
                    index=False,
                    columns=csv_cols,
                    encoding="utf-16",
                    header=False,
                )

                hdf5_cols = ["timestamp", "open", "high", "low", "close", "tickvol"]
                test_data[grp_names[i]] = df[hdf5_cols]

                grp_name = grp_names[i]
                sym = f.require_group(grp_name[:6])
                tf = sym.require_group(grp_name[6:])
                for key, val in data_dict.items():
                    if key in hdf5_cols:
                        x = val[: n // 3]
                        dset = tf.create_dataset(
                            name=key,
                            data=x,
                            dtype=x.dtype,
                            shape=x.shape,
                            maxshape=(None,),
                            compression="gzip",
                        )

        return rt, fn, test_data

    def test_successfully_creates_new_ohlc_data(self, tmp_data_csv_only):
        rt, df_list = tmp_data_csv_only
        trg = rt / "trg_data.hdf5"
        fxd.archive_data_from_csv(rt, trg)

        with h5py.File(trg, "a") as f:
            for key, df in df_list.items():
                sym = f[key[:6]]
                tf = sym[key[6:]]
                for dname in tf.keys():
                    assert np.array_equal(df[dname].values, tf[dname][:])

    def test_successfully_overwrites_old_data_with_newer_larger_data(
        self, tmp_data_csv_and_hdf5
    ):
        rt, trg, df_list = tmp_data_csv_and_hdf5
        fxd.archive_data_from_csv(rt, trg)

        with h5py.File(trg, "a") as f:
            for key, df in df_list.items():
                sym = f[key[:6]]
                tf = sym[key[6:]]
                for dname in tf.keys():
                    assert np.array_equal(df[dname].values, tf[dname][:])

    def test_deletes_source_files(self, tmp_data_csv_and_hdf5):
        rt, trg, df_list = tmp_data_csv_and_hdf5

        flist_before = glob.glob(str(rt) + "/**/*.csv", recursive=True)
        fxd.archive_data_from_csv(rt, trg)
        flist_after = glob.glob(str(rt) + "/**/*.csv", recursive=True)

        assert len(flist_before) > 0 and len(flist_after) == 0


class Test_archive_data_from_mt5:
    """Tests that archive_data_from_mt5() meets the following expectations:
    - Successfully creates new group with OHLCT data.
    - Successfully overwrites existing OHLCT data with newer, larger data.
    - Deletes closes MT5 connection after run.
    """

    @pytest.fixture(scope="function")
    def tmp_data_csv_only(self, tmp_path):
        rt = tmp_path / "data"
        rt.mkdir()
        return rt

    @pytest.fixture(scope="function")
    def tmp_data_csv_and_hdf5(self, tmp_path):
        symbols = ["EURUSD", "USDJPY"]
        rt = tmp_path / "data"
        rt.mkdir()
        fn = rt / "tmp_trg.hdf5"

        with h5py.File(fn, "a") as f:
            for sym in symbols:
                f.require_group(sym)

        return rt, fn, symbols

    def test_successfully_creates_new_ohlc_data(self, tmp_data_csv_only):
        rt = tmp_data_csv_only
        trg = rt / "trg_data.hdf5"
        symbols = ["EURUSD", "USDJPY"]
        frequencies = ["H1", "Daily"]
        nbars = 10
        timeframes = {
            key: val
            for key, val in fxd.AVAILABLE_FREQUENCIES.items()
            if key in frequencies
        }

        for sym in symbols:
            df_dict = {}
            for freq in frequencies:
                df = fxd.retrieve_data_from_mt5_server(
                    sym, timeframes[freq], nbars=nbars
                )
                df_dict[freq] = df
            fxd.archive_data_from_mt5(
                trg, symbols, frequencies=frequencies, nbars=nbars
            )

            with h5py.File(trg, "a") as f:
                for freq, df in df_dict.items():
                    sym_grp = f[sym]
                    tf_grp = sym_grp[freq]
                    for dname in tf_grp.keys():
                        assert np.array_equal(df[dname].values[:-1], tf_grp[dname][:-1])

    def test_successfully_overwrites_old_data_with_newer_larger_data(
        self, tmp_data_csv_and_hdf5
    ):
        rt, trg, symbols = tmp_data_csv_and_hdf5
        symbols = ["EURUSD", "USDJPY"]
        frequencies = ["H1", "Daily"]
        nbars = 100
        timeframes = {
            key: val
            for key, val in fxd.AVAILABLE_FREQUENCIES.items()
            if key in frequencies
        }

        for sym in symbols:
            df_dict = {}
            for freq in frequencies:
                df = fxd.retrieve_data_from_mt5_server(
                    sym, timeframes[freq], nbars=nbars
                )
                df_dict[freq] = df

            # First call: create datasets from partial data.
            fxd.archive_data_from_mt5(
                trg, symbols, frequencies=frequencies, nbars=nbars // 3
            )

            # Second call: update datasets with full data.
            fxd.archive_data_from_mt5(
                trg, symbols, frequencies=frequencies, nbars=nbars
            )

            with h5py.File(trg, "a") as f:
                for freq, df in df_dict.items():
                    sym_grp = f[sym]
                    tf_grp = sym_grp[freq]
                    for dname in tf_grp.keys():
                        assert np.array_equal(df[dname].values[:-1], tf_grp[dname][:-1])

    def test_closes_mt5_connection_after_run(self, tmp_data_csv_only):
        rt = tmp_data_csv_only
        trg = rt / "trg_data.hdf5"
        symbols = ["EURUSD", "USDJPY"]
        frequencies = ["H1", "Daily"]
        nbars = 10
        timeframes = {
            key: val
            for key, val in fxd.AVAILABLE_FREQUENCIES.items()
            if key in frequencies
        }

        for sym in symbols:
            df_dict = {}
            for freq in frequencies:
                df = fxd.retrieve_data_from_mt5_server(
                    sym, timeframes[freq], nbars=nbars
                )
                df_dict[freq] = df
            mt5.initialize(**fxd.ACCT_INFO)
            fxd.archive_data_from_mt5(
                trg, symbols, frequencies=frequencies, nbars=nbars
            )
            x = mt5.terminal_info()
            assert x is None
            mt5.shutdown()
