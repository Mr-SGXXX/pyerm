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

# Version: 0.3.3

from time import time
import pandas as pd
import numpy as np
import re
from datetime import datetime
import typing

from .dbbase import Database
from .dbbase import View

def auto_detect_def(param_dict:typing.Dict[str, typing.Any]) -> typing.Dict[str, str]:
    param_def_dict = {}
    for k, v in param_dict.items():
        param_def_dict[k] = value2def(v)
        if param_def_dict[k] == 'TEXT':
            try:
                param_dict[k] = str(v)
            except:
                raise TypeError(f'Unsupported type for DB: {type(v)}, consider to convert it to str or bytes.')
    return param_def_dict

def value2def(v):
    if isinstance(v, int):
        return 'INTEGER'
    elif isinstance(v, float):
        return 'REAL'
    elif isinstance(v, str):
        return 'TEXT'
    elif isinstance(v, bool):
        return f'INTEGER CHECK({v} IN (0, 1))'
    elif isinstance(v, bytes) or isinstance(v, bytearray):
        return 'BLOB'
    else:
        return 'TEXT'

def delete_failed_experiments(db:Database):
    experiment_table = db['experiment_list']
    failed_experiments = experiment_table.select('id', 'task', where="status='failed'")
    for experiment in failed_experiments:
        experiment_id = experiment[0]
        task = experiment[1]
        task_table = db[f"result_{task}"]
        task_table.delete(f"experiment_id={experiment_id}")
        experiment_table.delete(f"id={experiment_id}")

    # delete stuck running experiments that have been running for more than 24 hours
    running_experiments = experiment_table.select('id', 'task', 'start_time', where="status='running'")
    for experiment in running_experiments:
        experiment_id = experiment[0]
        task = experiment[1]
        if time() - datetime.strptime(experiment[2], "%Y-%m-%d %H:%M:%S").timestamp() > 86400:
            task_table = db[f"result_{task}"]
            task_table.delete(f"experiment_id={experiment_id}")
            experiment_table.delete(f"id={experiment_id}")

def get_result_statistics(db, task, method, method_id, data, data_id):
    same_setting_id_sql = f"SELECT id FROM experiment_list WHERE method='{method}' AND method_id={method_id} AND data='{data}' AND data_id={data_id} AND task='{task}' AND status='finished'"
    same_setting_id = db.conn.execute(same_setting_id_sql).fetchall()
    # print(same_setting_id)
    if len(same_setting_id) == 0:
        return None, []
    same_setting_id = [str(i[0]) for i in same_setting_id]
    return get_result_statistics_by_ids(db, task, same_setting_id), same_setting_id
    
def get_result_statistics_by_ids(db, task, same_setting_id):
    result_table = db[f'result_{task}']
    score_columns = [col for col in result_table.columns if not col.startswith("image_") and not col=="experiment_id"]
    same_setting_id_sql = ','.join(same_setting_id)
    # print(same_setting_id_sql)
    
    max_score_sql = f"SELECT {','.join([f'MAX({col}) AS {col}' for col in score_columns])} FROM result_{task} WHERE experiment_id IN ({same_setting_id_sql})"
    max_score = pd.read_sql_query(max_score_sql, db.conn)
    min_score_sql = f"SELECT {','.join([f'MIN({col}) AS {col}' for col in score_columns])} FROM result_{task} WHERE experiment_id IN ({same_setting_id_sql})"
    min_score = pd.read_sql_query(min_score_sql, db.conn)
    avg_score_sql = f"SELECT {','.join([f'AVG({col}) AS {col}' for col in score_columns])} FROM result_{task} WHERE experiment_id IN ({same_setting_id_sql})"
    avg_score = pd.read_sql_query(avg_score_sql, db.conn)


    std_queries = [
        f"""(SELECT AVG(({col} - sub.avg_{col}) * ({col} - sub.avg_{col})) AS var_{col}
             FROM result_{task}, 
             (SELECT AVG({col}) AS avg_{col} FROM result_{task} WHERE experiment_id IN ({same_setting_id_sql})) AS sub
             WHERE experiment_id IN ({same_setting_id_sql})) AS var_{col}"""
        for col in score_columns
    ]
    std_score_sql = f"SELECT {', '.join(std_queries)}"
    var_score = pd.read_sql_query(std_score_sql, db.conn)
    std_score = var_score.apply(np.sqrt)
    std_score.columns = [col.replace('var_', '') for col in std_score.columns]
    
    
    median_queries = [
        f"""(SELECT AVG({col}) FROM 
            (SELECT {col} FROM result_{task} 
             WHERE experiment_id IN ({same_setting_id_sql}) 
             ORDER BY {col} 
             LIMIT 2 - (SELECT COUNT(*) FROM result_{task} 
                        WHERE experiment_id IN ({same_setting_id_sql})) % 2 
             OFFSET (SELECT (COUNT(*) - 1) / 2 FROM result_{task} 
                     WHERE experiment_id IN ({same_setting_id_sql}))) AS median_{col}) AS {col}"""
        for col in score_columns
    ]
    median_score_sql = f"SELECT {', '.join(median_queries)}"
    median_score = pd.read_sql_query(median_score_sql, db.conn)
    rst = pd.concat([max_score, min_score, avg_score, std_score, median_score], axis=0)
    rst.index = ['Max', 'Min', 'Avg', 'Std', 'Median']
    return rst
    
    
    
def split_result_info(result_info:pd.DataFrame):
    columns_keep = [col for col in result_info.columns if not col.startswith("image_") and not col=="experiment_id"]
    pattern = re.compile(r'image_(\d+)$')
    image_dict = {}
    for name in result_info.columns:
        match = pattern.match(name)
        if match and not result_info[name].isnull().all():
            image_dict[result_info[f"{name}_name"][0]] = result_info[name][0]
        elif result_info[name].isnull().all():
            break
    
    return result_info[columns_keep], image_dict


def experiment_id2remark_name(db, experiment_id):
    task, remark_name = db['experiment_list'].select('task', 'remark', where=f'id={experiment_id}')[0]
    return remark_name if remark_name else f"{task}_{experiment_id}"

def method_id2remark_name(db, method, method_id):
    if f'method_{method}' not in db.table_names and f'method_{method}' not in db.view_names:
        return f"{method_id}"
    if not (isinstance(method_id, int) and method_id > 0):
        return f"{method_id}"
    remark_name = db[f'method_{method}'].select('remark', where=f'method_id={method_id}')[0][0]
    return remark_name if remark_name else f"{method_id}"

def data_id2remark_name(db, data, data_id):
    if f'data_{data}' not in db.table_names and f'data_{data}' not in db.view_names:
        return f"{data_id}"
    if not (isinstance(data_id, int) and data_id > 0):
        return f"{data_id}"
    remark_name = db[f'data_{data}'].select('remark', where=f'data_id={data_id}')[0][0]
    return remark_name if remark_name else f"{data_id}"

def experiment_remark_name2id(db, remark_name):
    try:
        return db['experiment_list'].select('id', where=f'remark="{remark_name}"')[0][0]
    except:
        if remark_name.isnumeric():
            return int(remark_name)
        return -1
    
def method_remark_name2id(db, method, remark_name):
    if f'method_{method}' not in db.table_names and f'method_{method}' not in db.view_names:
        return -1
    try:
        return db[f'method_{method}'].select('method_id', where=f'remark="{remark_name}"')[0][0]
    except:
        if remark_name.isnumeric():
            return int(remark_name)
        return -1

def data_remark_name2id(db, data, remark_name):
    if f'data_{data}' not in db.table_names and f'data_{data}' not in db.view_names:
        return -1
    try:
        return db[f'data_{data}'].select('data_id', where=f'remark="{remark_name}"')[0][0]
    except:
        if remark_name.isnumeric():
            return int(remark_name)
        return -1
    