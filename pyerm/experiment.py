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

# Version: 0.1.0

import os
import typing
from PIL import Image

from .dbbase import Database
from .tables import ExperimentTable, ParameterTable, ResultTable, DetailTable, DataTable

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

        self.id = None
        self.data = None
        self.data_id = None
        self.method = None
        self.method_id = None
        self.task = None

    def experiment_start(self, description:str, start_time:float=None, tags:str=None) -> int:
        assert self.data is not None, 'Data not initialized, run data_init() first'
        assert self.method is not None, 'Method not initialized, run method_init() first'
        assert self.task is not None, 'Task not initialized, run task_init() first'
        self.id = self.experiment_table.experiment_start(description, self.method, self.method_id, self.data, self.data_id, self.task, start_time, tags)
    
    def experiment_over(self, rst_dict:typing.Dict[str, typing.Any], images:typing.List[typing.Union[Image.Image, str]], end_time:float=None, useful_time_cost:float=None) -> None:
        assert self.id is not None, 'Experiment not started, run experiment_start() first'
        assert len(rst_dict) == len(self.rst_table.columns) - self.rst_table.max_image_num - 3, 'Result definition and result dict length mismatch'
        self.rst_table.record_rst(experiment_id=self.id, **rst_dict)
        self.rst_table.record_image(self.id, images)
        self.experiment_table.experiment_over(self.id, end_time=end_time, useful_time_cost=useful_time_cost)

    def experiment_failed(self, end_time:float=None) -> None:
        assert self.id is not None, 'Experiment not started, run experiment_start() first'
        self.experiment_table.experiment_failed(self.id, end_time=end_time)

    def detail_update(self, detail_dict:typing.Dict[str, typing.Any]):
        assert self.id is not None, 'Experiment not started, run experiment_start() first'
        assert len(detail_dict) == len(self.detail_table.columns) - 2, 'Detail definition and detail dict length mismatch'
        self.detail_table.insert(experiment_id=self.id, **detail_dict)

    def data_init(self, data_name:str, param_def_dict:typing.Dict[str, str], param_dict:typing.Dict[str, typing.Any]):
        assert len(param_def_dict) == len(param_dict), 'Parameter definition and parameter dict length mismatch'
        self.data = data_name
        self.data_table = DataTable(self.db, data_name, param_def_dict)
        self.data_id = self.data_table.insert(**param_dict)
    
    def method_init(self, method_name:str, param_def_dict:typing.Dict[str, str], param_dict:typing.Dict[str, typing.Any], detail_def_dict:typing.Dict[str, str]):
        assert len(param_def_dict) == len(param_dict), 'Parameter definition and parameter dict length mismatch'
        self.method = method_name
        self.method_table = ParameterTable(self.db, method_name, param_def_dict)
        self.method_id = self.method_table.insert(**param_dict)
        self.detail_table = DetailTable(self.db, method_name, detail_def_dict)

    def task_init(self, task_name:str, rst_def_dict:typing.Dict[str, str], max_image_num:int=10):
        self.task = task_name
        self.rst_table = ResultTable(self.db, task_name, rst_def_dict, max_image_num)

