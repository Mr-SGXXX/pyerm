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

from PIL import Image
from io import BytesIO
from time import strftime, time, localtime
import typing
import traceback

from .dbbase import Table, Database

class ExperimentTable(Table):
    def __init__(self, db: Database) -> None:
        columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'description': 'TEXT DEFAULT NULL',
            'method': 'TEXT NOT NULL',
            'method_id': 'INTEGER NOT NULL', 
            'data': 'TEXT NOT NULL',
            'data_id': 'INTEGER NOT NULL',
            'task': 'TEXT NOT NULL',
            'tags': 'TEXT DEFAULT NULL', # 'tag1,tag2,tag3,...'
            'experimenters': 'TEXT DEFAULT NULL', # 'experimenter1,experimenter2,experimenter3,...'
            'start_time': 'DATETIME',
            'end_time': 'DATETIME DEFAULT NULL',
            'useful_time_cost': 'REAL DEFAULT NULL',
            'total_time_cost': 'REAL AS (strftime(\"%s\", end_time) - strftime(\"%s\", start_time)) VIRTUAL',
            'status': 'TEXT CHECK(status IN (\"running\", \"finished\", \"failed\"))',
            'failed_reason': 'TEXT DEFAULT NULL',
        }
        super().__init__(db, "experiment_list", columns)

    def experiment_start(self, description:str, method:str, method_id:int, data:str, data_id, task:str, start_time:float=None, tags:str=None, experimenters:str=None) -> int:
        if start_time is None:
            start_time = time()
        start_time = localtime(start_time)
        start_time = strftime("%Y-%m-%d %H:%M:%S", start_time)
        return super().insert(description=description, method=method, method_id=method_id, data=data, data_id=data_id, task=task, tags=tags, experimenters=experimenters, start_time=strftime(start_time), status='running')

    def experiment_over(self, experiment_id:int, end_time:float=None, useful_time_cost:float=None) -> None:
        if end_time is None:
            end_time = time()
        end_time = localtime(end_time)
        end_time = strftime("%Y-%m-%d %H:%M:%S", end_time)
        super().update(f"id={experiment_id}", end_time=strftime(end_time), useful_time_cost=useful_time_cost, status='finished')

    def experiment_failed(self, experiment_id:int, end_time:float=None) -> None:
        if end_time is None:
            end_time = time()
        end_time = localtime(end_time)
        end_time = strftime("%Y-%m-%d %H:%M:%S", end_time)
        error_info = traceback.format_exc()
        super().update(f"id={experiment_id}", end_time=strftime(end_time), status='failed', failed_reason=error_info)

    def get_experiment(self, experiment_id:int) -> dict:
        return super().select(where=f"id={experiment_id}")[0]
    
    def __getitem__(self, index: int):
        return self.get_experiment(index)

class DataTable(Table):
    def __init__(self, db: Database, data: str, param_def_dict: dict=None) -> None:
        table_name = f"data_{data}"
        if table_name in db.table_names:
            columns = None
        else:
            assert param_def_dict is not None, 'Data Parameter Dict must be provided when creating a new data table'
            columns = {
                'data_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                **param_def_dict,
            }
        super().__init__(db, table_name, columns)
        if len(param_def_dict) != 0: 
            self.db.cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS index_{table_name} ON {table_name}({', '.join(param_def_dict.keys())})")
    
    def insert(self, **kwargs):
        condition = ' AND '.join([f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in kwargs.items()])
        id_list = self.db.cursor.execute(f"SELECT data_id FROM {self.table_name} WHERE {condition}").fetchall()
        if id_list == []:
            return super().insert(**kwargs)
        else:
            return id_list[0][0] 


class MethodTable(Table):
    def __init__(self, db: Database, method: str, param_def_dict: dict=None) -> None:
        table_name = f"method_{method}"
        if table_name in db.table_names:
            columns = None
        else:
            assert param_def_dict is not None, 'Method Parameter Dict must be provided when creating a new parameter table'
            columns = {
                'method_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                **param_def_dict,
            }
        super().__init__(db, table_name, columns)
        if len(param_def_dict) != 0: 
            self.db.cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS index_{table_name} ON {table_name}({', '.join(param_def_dict.keys())})")
    
    def insert(self, **kwargs):
        condition = ' AND '.join([f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in kwargs.items()])
        id_list = self.db.cursor.execute(f"SELECT method_id FROM {self.table_name} WHERE {condition}").fetchall()
        if id_list == []:
            return super().insert(**kwargs)
        else:
            return id_list[0][0] 

class ResultTable(Table):
    def __init__(self, db: Database, task: str, rst_def_dict: dict=None, max_image_num: int=10) -> None:
        columns = {
            'experiment_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            **{f'image_{i}': 'BLBO DEFAULT NULL' for i in range(max_image_num)},
            **rst_def_dict,
        }
        table_name = f"result_{task}"
        super().__init__(db, table_name, columns)
        self.max_image_num = max_image_num

    def record_rst(self, experiment_id:int, **rst_dict:dict):
        self.insert(experiment_id=experiment_id, **rst_dict)

    def record_image(self, experiment_id:int, image_list:typing.List[typing.Union[Image.Image, str]]=[]):
        for i, image in enumerate(image_list):
            if isinstance(image, Image.Image):
                image = BytesIO()
                image_list[i].save(image, format='PNG')
                image = image.getvalue()
            elif isinstance(image, str):
                image = open(image, 'rb').read()
            self.update(f"experiment_id={experiment_id}", **{f'image_{i}': image})


class DetailTable(Table):
    def __init__(self, db: Database, method: str, detail_def_dict: dict=None) -> None:
        columns = {
            'detail_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'experiment_id': 'INTEGER FOREIGN KEY REFERENCES experiment_list(id)',
            **detail_def_dict,
        }
        table_name = f"detail_\'{method}\'"
        super().__init__(db, table_name, columns)