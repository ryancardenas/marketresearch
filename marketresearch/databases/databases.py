#!/usr/bin/env python
"""Copyright 2022 Ryan Cardenas
Name: databases
Project: marketresearch
Author: Ryan Cardenas
Creation Date: 11/8/2022

Database classes that provide an interface between a source of data and a DataFeed or Timeframe.
"""

from pathlib import Path
from typing import Union

import h5py

import marketresearch.abstractions.abstractions as abmr


class HDF5CandlestickDataBase(abmr.AbstractCandlestickDataBase):
    """A DataBase that provides OHLCTV data from an HDF5 file. Assumes the following file structure:
    HDF5_FILE/
        SYMBOL_1/
            TIMEFRAME_1/
                TIMESTAMP
                OPEN
                HIGH
                LOW
                CLOSE
                VOLUME
            TIMEFRAME_2/...
        SYMBOL_2/
            TIMEFRAME_1/...
        SYMBOL_3/...
    """

    def __init__(self, name: str, src_fn: Union[str, Path], file_mode: str = "r"):
        super().__init__(name=name, src_fn=src_fn, file_mode=file_mode)

    def connect(self):
        """Loads an HDF5 file. If a file is already loaded, closes that file first and then loads."""
        if isinstance(self.f, h5py._hl.files.File):
            self.f.close()
        self.f = h5py.File(self.src_fn, self.file_mode)

    def update(self):
        """NOT YET IMPLEMENTED."""
        # if self.file_mode not in ['a']:
        #     raise IOError(f"file_mode ('{self.file_mode}') not valid for appending data to existing database; must "
        #                   f"use file_mode 'a'")
        # else:
        #     #ToDo: implement HDF5CandlestickDataBase.update()
        #     pass
        pass

    def retrieve_dataset(self, symbol: str, timeframe: str, dataset: str):
        translated_timeframe = self.translate_timeframe(timeframe)
        return self.f[symbol][translated_timeframe][dataset]

    @staticmethod
    def translate_timeframe(timeframe):
        if timeframe in ['D1', 'D']:
            translated = 'Daily'
        elif timeframe in ['W1', 'W']:
            translated = 'Weekly'
        elif timeframe in ['M1', 'M']:
            translated = 'Monthly'
        elif timeframe[0] == 'm':
            translated = 'M' + timeframe[1:]
        else:
            translated = timeframe
        return translated
