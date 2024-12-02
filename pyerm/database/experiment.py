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

# Version: 0.3.2

import os
import typing
from PIL import Image
import traceback
import sys
from copy import deepcopy

from .dbbase import Database
from .tables import ExperimentTable, MethodTable, ResultTable, DetailTable, DataTable
from .utils import auto_detect_def

PYERM_HOME = os.path.join(os.path.expanduser('~'), 'pyerm')
__all__ = ['Experiment']


class Experiment:
    """
    Experiment class for database operation
    
    Parameters
    ----------
    db_path : str, optional
        The path of the database file, by default None, which means the database file will be saved in the user's home directory
        
    Attributes
    ----------
    experiment_table : ExperimentTable
        The experiment table object, saves the experiment information and connects the other tables
    parameter_table : MethodTable
        The parameter table object, saves the parameters of the method
    rst_table : ResultTable
        The result table object, saves the results of the method
    detail_table : DetailTable  
        The detail table object, saves the details of the method
    data_table : DataTable
        The data table object, saves the dataset information and parameters of the method
    run_times : int
        The number of experiments that have been run for the current 'Experiment' instance

    Usage
    -----
    >>> exp = Experiment()
    >>> exp.data_init('data', {'data_param1': 1, 'data_param2': 2})
    >>> exp.method_init('method', {'method_param1': 3, 'method_param2': 4})
    >>> exp.task_init('task')
    >>> exp.experiment_start('description')
    >>> exp.detail_update({'detail_info1': 7, 'detail_info2': 8})
    >>> exp.experiment_over(rst_dict={'result_score1': 9, 'result_score2': 10}, image_dict={'image1': Image.open('1.png'), 'image2': '2.png'})

    For more detailed example, please refer to the 'examples' directory

    """
    def __init__(self, db_path:str=None):
        if db_path is None:
            db_path = os.path.join(PYERM_HOME, 'experiment.db')
        self._db = Database(db_path)
        self.experiment_table = ExperimentTable(self._db)
        self.parameter_table = None
        self.rst_table = None
        self.detail_table = None
        self.data_table = None
        self.run_times = 0

        self._id = None
        self._data = None
        self._data_id = None
        self._method = None
        self._method_id = None
        self._task = None

    def experiment_start(self, description:str=None, start_time:float=None, tags:typing.Union[typing.List[str], str]=None, experimenters:typing.Union[typing.List[str], str]=None) -> int:
        """
        Start an experiment, and record the experiment information in the database
        
        core function of the Experiment class,

        essential: run data_init(), method_init(), task_init() first

        Parameters
        ----------
        description : str, optional
            The description of the experiment, by default None, which means the description is empty
        start_time : float, optional
            The start time of the experiment, by default None, which means the current time
        tags : str, optional
            The tags of the experiment, by default None
        experimenters : str, optional
            The experimenters of the experiment, by default None

        Returns
        -------
        int
            The experiment ID

        """
        def handle_exception(exc_type, exc_value, exc_traceback):
            error_info = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self.experiment_table.experiment_failed(self._id, error_info)
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        assert self._data is not None, 'Data not initialized, run data_init() first'
        assert self._method is not None, 'Method not initialized, run method_init() first'
        assert self._task is not None, 'Task not initialized, run task_init() first'
        if tags is not None and isinstance(tags, typing.List):
            tags = ','.join(tags)
        if experimenters is not None and isinstance(experimenters, typing.List):
            experimenters = ','.join(experimenters)
        self._id = self.experiment_table.experiment_start(description, self._method, self._method_id, self._data, self._data_id, self._task, start_time, tags, experimenters)
        self.run_times += 1
        sys.excepthook = handle_exception
        return self._id
    
    def experiment_over(self, rst_dict:typing.Dict[str, typing.Any], image_dict:typing.Dict[str, typing.Union[Image.Image, str, bytearray, bytes]]={}, end_time:float=None, useful_time_cost:float=None) -> None:
        """
        Finish an experiment, and record the result in the database
        When the experiment is failed, the failed information will be automatically recorded in the database
        
        core function of the Experiment class,

        essential: run experiment_start() first
        
        Parameters
        ----------
        rst_dict : typing.Dict[str, typing.Any]
            The result dictionary, contains the result of the experiment, such as {'score1': 1, 'score2': 2}
        image_dict : typing.Dict[str, typing.Union[Image.Image, str, bytearray, bytes]], optional
            The image dictionary, contains the image data of the experiment, such as {'image1': Image.open('1.png'), 'image2': '2.png'}, by default no image
        end_time : float, optional
            The end time of the experiment, by default None, which means the current time
        useful_time_cost : float, optional
            The useful time cost of the experiment, by default None, used to record the user-defined time cost

        """
        assert self._id is not None, 'Experiment not started, run experiment_start() first'
        assert self.rst_table is None or set(rst_dict.keys()).issubset(set(self.rst_table.non_img_columns)), 'Result definition mismatch'
        rst_dict = deepcopy(rst_dict)
        if self.rst_table is None:
            rst_def_dict = auto_detect_def(rst_dict)
            self.rst_table = ResultTable(self._db, self._task, rst_def_dict)
        self.rst_table.record_rst(experiment_id=self._id, **rst_dict)
        self.rst_table.record_image(self._id, **image_dict)
        self.experiment_table.experiment_over(self._id, end_time=end_time, useful_time_cost=useful_time_cost)
        self._id = None
        sys.excepthook = sys.__excepthook__
        

    def experiment_failed(self, error_info:str, end_time:float=None) -> None:
        """
        Mark the experiment as failed, and record the reason in the database
        
        optional function of the Experiment class, use it where you want to mark the experiment as failed

        essential: run experiment_start() first

        Parameters
        ----------
        error_info : str
            The error information of the experiment

        end_time : float, optional
            The end time of the experiment, by default None, which means the current time

        """
        assert self._id is not None, 'Experiment not started, run experiment_start() first'
        self.experiment_table.experiment_failed(self._id, error_info, end_time=end_time)
        self._id = None
        

    def detail_update(self, detail_dict:typing.Dict[str, typing.Any]):
        """
        Update the detail information what you need of the experiment, such as the ML training process, etc.
        It will automatically record the time when the detail information is updated
        
        optional function of the Experiment class, use it for better tracking the experiment
        make sure the detail_dict has consistent format

        essential: run experiment_start() first

        Parameters
        ----------
        detail_dict : typing.Dict[str, typing.Any]
            The detail dictionary, contains the detail information of the experiment, such as {'epoch': 100, 'loss': 0.1, 'accuracy': 0.9}


        """
        assert self._id is not None, 'Experiment not started, run experiment_start() first'
        assert len(detail_dict) == len(self.detail_table.columns) - 2, 'Detail definition and detail dict length mismatch'
        detail_dict = deepcopy(detail_dict)
        if self.detail_table is None:
            detail_def_dict = auto_detect_def(detail_dict)
            self.detail_table = DetailTable(self._db, self._id, detail_def_dict)
        self.detail_table.insert(experiment_id=self._id, **detail_dict)

    def data_init(self, data_name:str, param_dict:typing.Dict[str, typing.Any]=None, param_def_dict:typing.Dict[str, str]=None):
        """
        Initialize the data table, and insert the data information into the database, such as the dataset preproessing parameters, etc.
        
        core function of the Experiment class, run it before experiment_start()

        Parameters
        ----------
        data_name : str
            The name of the data table, such as 'data'
        param_dict : typing.Dict[str, typing.Any], optional
            The parameter dictionary, contains the data information, by default None
        param_def_dict : typing.Dict[str, str], optional
            The parameter definition dictionary, contains the data parameter definition, by default None, which means the parameter definition will be automatically detected
        
        Returns
        -------
        int
            The data ID

        """
        assert " " not in data_name, 'Data name cannot contain space'
        assert param_def_dict is None or len(param_def_dict) == len(param_dict), 'Parameter definition and parameter dict length mismatch'
        self._data = data_name
        param_dict = deepcopy(param_dict)
        if len(param_dict) == 0:
            self._data_id = -1
            print(f"No parameter for table data_{data_name}, table creating canceled")
            return
        if param_def_dict is None:
            param_def_dict = auto_detect_def(param_dict)
        self.data_table = DataTable(self._db, data_name, param_def_dict)
        self._data_id = self.data_table.insert(**param_dict)
        return self._data_id
    
    def method_init(self, method_name:str, param_dict:typing.Dict[str, typing.Any]=None, param_def_dict:typing.Dict[str, str]=None, detail_def_dict:typing.Dict[str, str]=None):
        """
        Initialize the method table, and insert the method information into the database, such as the method parameters, etc.

        core function of the Experiment class, run it before experiment_start()

        Parameters
        ----------
        method_name : str
            The name of the method table, such as 'method'
        param_dict : typing.Dict[str, typing.Any], optional
            The parameter dictionary, contains the method information, by default None
        param_def_dict : typing.Dict[str, str], optional
            The parameter definition dictionary, contains the method parameter definition, by default None, which means the parameter definition will be automatically detected

        Returns
        -------
        int
            The method ID

        """
        assert " " not in method_name, 'Method name cannot contain space'
        assert param_def_dict is None or len(param_def_dict) == len(param_dict), 'Parameter definition and parameter dict length mismatch'
        self._method = method_name
        param_dict = deepcopy(param_dict)
        if detail_def_dict is not None:
            self.detail_table = DetailTable(self._db, method_name, detail_def_dict)
        if len(param_dict) == 0:
            self._method_id = -1
            print(f"No parameter for table method_{method_name}, table creating canceled")
            return
        if param_def_dict is None:
            param_def_dict = auto_detect_def(param_dict)
        self.method_table = MethodTable(self._db, method_name, param_def_dict)
        self._method_id = self.method_table.insert(**param_dict)
        return self._method_id


    def task_init(self, task_name:str, rst_def_dict:typing.Dict[str, str]=None):
        """
        Initialize the result table, and insert the result information into the database, such as the result parameters, etc.

        core function of the Experiment class, run it before experiment_start()

        Parameters
        ----------
        task_name : str
            The name of the task table, such as 'task'
        rst_def_dict : typing.Dict[str, str], optional
            The result definition dictionary, contains the result parameter definition, by default None, which means the parameter definition will be automatically detected when the result is recorded

        """
        assert " " not in task_name, 'Task name cannot contain space'
        self._task = task_name
        if rst_def_dict is not None:
            self.rst_table = ResultTable(self._db, task_name, rst_def_dict)





