# MIT License

# Copyright (c) 2024 Yuxuan Shao

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Version: 0.2.3

import os
import typing
from PIL import Image
import atexit

from .dbbase import Database
from .tables import ExperimentTable, MethodTable, ResultTable, DetailTable, DataTable

__all__ = ['Experiment']

USER_HOME = os.path.expanduser('~')

class Experiment:
    def __init__(self, db_path:str=None):
        if db_path is None:
            db_path = os.path.join(USER_HOME, 'experiment.db')
        self.db = Database(db_path)
        self.experiment_table = ExperimentTable(self.db)
        self.parameter_table = None
        self.rst_table = None
        self.detail_table = None
        self.data_table = None

        self._id = None
        self._data = None
        self._data_id = None
        self._method = None
        self._method_id = None
        self._task = None

    def experiment_start(self, description:str=None, start_time:float=None, tags:str=None, experimenters:str=None) -> int:
        assert self._data is not None, 'Data not initialized, run data_init() first'
        assert self._method is not None, 'Method not initialized, run method_init() first'
        assert self._task is not None, 'Task not initialized, run task_init() first'
        self._id = self.experiment_table.experiment_start(description, self._method, self._method_id, self._data, self._data_id, self._task, start_time, tags, experimenters)
        atexit.register(self.experiment_table.experiment_failed, self._id)
    
    def experiment_over(self, rst_dict:typing.Dict[str, typing.Union[int, float, str, bool, bytearray, bytes]], images:typing.List[typing.Union[Image.Image, str]]=[], end_time:float=None, useful_time_cost:float=None) -> None:
        assert self._id is not None, 'Experiment not started, run experiment_start() first'
        assert self.rst_table is None or len(rst_dict) <= len(self.rst_table.columns) - self.rst_table.max_image_num - 1, 'Result definition and result dict length mismatch'
        if self.rst_table is None:
            rst_def_dict = auto_detect_def(rst_dict)
            self.rst_table = ResultTable(self.db, self._task, rst_def_dict)
        self.rst_table.record_rst(experiment_id=self._id, **rst_dict)
        self.rst_table.record_image(self._id, images)
        self.experiment_table.experiment_over(self._id, end_time=end_time, useful_time_cost=useful_time_cost)
        atexit.unregister(self.experiment_table.experiment_failed)

    def experiment_failed(self, end_time:float=None) -> None:
        assert self._id is not None, 'Experiment not started, run experiment_start() first'
        self.experiment_table.experiment_failed(self._id, end_time=end_time)
        

    def detail_update(self, detail_dict:typing.Dict[str, typing.Union[int, float, str, bool, bytearray, bytes]]):
        assert self._id is not None, 'Experiment not started, run experiment_start() first'
        assert len(detail_dict) == len(self.detail_table.columns) - 2, 'Detail definition and detail dict length mismatch'
        if self.detail_table is None:
            detail_def_dict = auto_detect_def(detail_dict)
            self.detail_table = DetailTable(self.db, self._method, detail_def_dict)
        self.detail_table.insert(experiment_id=self._id, **detail_dict)

    def data_init(self, data_name:str, param_dict:typing.Dict[str, typing.Union[int, float, str, bool, bytearray, bytes]], param_def_dict:typing.Dict[str, str]=None):
        assert param_def_dict is None or len(param_def_dict) == len(param_dict), 'Parameter definition and parameter dict length mismatch'
        self._data = data_name
        if len(param_dict) == 0:
            self._data_id = -1
            print(f"No parameter for table data_{data_name}, table creating canceled")
            return
        if param_def_dict is None:
            param_def_dict = auto_detect_def(param_dict)
        self.data_table = DataTable(self.db, data_name, param_def_dict)
        self._data_id = self.data_table.insert(**param_dict)
    
    def method_init(self, method_name:str, param_dict:typing.Dict[str, typing.Union[int, float, str, bool, bytearray, bytes]], param_def_dict:typing.Dict[str, str]=None, detail_def_dict:typing.Dict[str, str]=None):
        assert param_def_dict is None or len(param_def_dict) == len(param_dict), 'Parameter definition and parameter dict length mismatch'
        self._method = method_name
        if detail_def_dict is not None:
            self.detail_table = DetailTable(self.db, method_name, detail_def_dict)
        if len(param_dict) == 0:
            self._method_id = -1
            print(f"No parameter for table method_{method_name}, table creating canceled")
            return
        if param_def_dict is None:
            param_def_dict = auto_detect_def(param_dict)
        self.method_table = MethodTable(self.db, method_name, param_def_dict)
        self._method_id = self.method_table.insert(**param_dict)


    def task_init(self, task_name:str, rst_def_dict:typing.Dict[str, str]=None, max_image_num:int=10):
        self._task = task_name
        if rst_def_dict is not None:
            self.rst_table = ResultTable(self.db, task_name, rst_def_dict, max_image_num)


def auto_detect_def(param_dict:typing.Dict[str, typing.Union[int, float, str, bool, bytearray, bytes]]) -> typing.Dict[str, str]:
    param_def_dict = {}
    for k, v in param_dict.items():
        if isinstance(v, int):
            param_def_dict[k] = 'INTEGER'
        elif isinstance(v, float):
            param_def_dict[k] = 'REAL'
        elif isinstance(v, str):
            param_def_dict[k] = 'TEXT'
        elif isinstance(v, bool):
            param_def_dict[k] = f'INTEGER CHECK({k} IN (0, 1))'
        elif isinstance(v, bytes) or isinstance(v, bytearray):
            param_def_dict[k] = 'BLOB'
        else:
            try:
                param_dict[k] = str(param_dict[k])
                param_def_dict[k] = 'TEXT'
            except:
                raise TypeError(f'Unsupported type for DB: {type(v)}')
    return param_def_dict
