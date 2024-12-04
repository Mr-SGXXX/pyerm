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

from PIL import Image
from io import BytesIO
import re
from time import strftime, time, localtime
import typing
import traceback
import sys

from .dbbase import Table, Database
from .utils import value2def

class ExperimentTable(Table):
    def __init__(self, db: Database) -> None:
        columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'remark': 'TEXT DEFAULT NULL UNIQUE',
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

    def experiment_failed(self, experiment_id:int, error_info:str=None, end_time:float=None) -> None:
        if end_time is None:
            end_time = time()
        end_time = localtime(end_time)
        end_time = strftime("%Y-%m-%d %H:%M:%S", end_time)
        # print(error_info)
        if error_info is None:
            error_info = traceback.format_exc()
            # print(error_info)
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
                'remark': 'TEXT DEFAULT NULL UNIQUE',
                **param_def_dict,
            }
        super().__init__(db, table_name, columns)
        # if len(param_def_dict) != 0: 
        #     self.db.cursor.execute(f"CREATE INDEX IF NOT EXISTS index_{self.table_name} ON {self.table_name}({', '.join(param_def_dict.keys())})")
    
    def insert(self, **kwargs):
        for key in kwargs.keys():
            if key not in self.columns:
                def_str = value2def(kwargs[key])
                self.add_column(key, def_str)
                self.update(**{key: 'NULL'})
        condition = ' AND '.join([f'{k.replace(" ", "_")}=?' for k in kwargs.keys()])
        values = list(kwargs.values())

        query = f"SELECT data_id FROM {self.table_name} WHERE {condition}"
        id_list = self.db.cursor.execute(query, values).fetchall()
        # print(kwargs)

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
                'remark': 'TEXT DEFAULT NULL UNIQUE',
                **param_def_dict,
            }
        super().__init__(db, table_name, columns)
        # if len(param_def_dict) != 0: 
        #     self.db.cursor.execute(f"CREATE INDEX IF NOT EXISTS index_{self.table_name} ON {self.table_name}({', '.join(param_def_dict.keys())})")
    
    def insert(self, **kwargs):
        for key in kwargs.keys():
            if key not in self.columns:
                self.add_column(key, value2def(kwargs[key]))
                self.update(**{key: 'NULL'})
        condition = ' AND '.join([f'{k.replace(" ", "_")}=?' for k in kwargs.keys()])
        values = list(kwargs.values())

        query = f"SELECT method_id FROM {self.table_name} WHERE {condition}"
        id_list = self.db.cursor.execute(query, values).fetchall()
        # print(kwargs)
        if id_list == []:
            return super().insert(**kwargs)
        else:
            return id_list[0][0] 

def image_def(i):
    return {f'image_{i}_name': 'TEXT DEFAULT NULL', f'image_{i}': 'BLOB DEFAULT NULL'}

class ResultTable(Table):
    def __init__(self, db: Database, task: str, rst_def_dict: dict=None, default_image_num: int=2) -> None:
        table_name = f"result_{task}"
        if table_name in db.table_names:
            columns = None
        else:
            assert rst_def_dict is not None, 'Result Dict must be provided when creating a new result table'
            columns = {
                'experiment_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                **rst_def_dict,
                **{k:v for i in range(default_image_num) for k,v in image_def(i).items()},
            }
        
        super().__init__(db, table_name, columns)
        self._non_img_columns = None
        pattern = re.compile(r'image_(\d+)')
        self.max_image_index = -1
        for name in self.columns:
            match = pattern.match(name)
            if match:
                self.max_image_index = max(self.max_image_index, int(match.group(1)))

    def record_rst(self, experiment_id:int, **rst_dict:dict):
        for key in rst_dict.keys():
            if key not in self.columns:
                self.add_column(key, value2def(rst_dict[key]))
        self.insert(experiment_id=experiment_id, **rst_dict)

    def record_image(self, experiment_id:int, **image_dict:typing.Dict[str, typing.Union[Image.Image, str, bytearray, bytes]]):        
        for i, image_key in enumerate(image_dict.keys()):
            if i > self.max_image_index:
                self.add_column(f'image_{i}_name', 'TEXT DEFAULT NULL')
                self.add_column(f'image_{i}', 'BLOB DEFAULT NULL')
                self.max_image_index += 1
            if isinstance(image_dict[image_key], Image.Image):
                image = BytesIO()
                image_dict[image_key].save(image, format='PNG')
                image = image.getvalue()
            elif isinstance(image_dict[image_key], str):
                image = open(image_dict[image_key], 'rb').read()
            # print(type(image_key))
            # print(type(image))
            self.update(f"experiment_id={experiment_id}", **{f'image_{i}_name': image_key})
            self.update(f"experiment_id={experiment_id}", **{f'image_{i}': image})
    
    @property
    def non_img_columns(self):
        if self._non_img_columns is None:
            self._non_img_columns = [c for c in self.columns if not c.startswith('image_')]
        return self._non_img_columns



class DetailTable(Table):
    def __init__(self, db: Database, experiment_id:int, detail_def_dict: dict=None) -> None:
        columns = {
            'detail_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            **detail_def_dict,
            'record_time': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        }
        table_name = f"detail_{experiment_id}"
        super().__init__(db, table_name, columns)
        
    def insert(self, **kwargs):
        cur_time = strftime("%Y-%m-%d %H:%M:%S", localtime(time()))
        kwargs['record_time'] = strftime(cur_time)
        return super().insert(**kwargs)