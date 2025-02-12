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

# Version: 0.3.6

import pandas as pd
import streamlit as st
import os
from PIL import Image
import re
import io
import matplotlib.pyplot as plt
import seaborn as sns
import typing
import datetime

from pyerm.database.dbbase import Database
from pyerm.database.experiment import Experiment
from pyerm.database.utils import data_id2remark_name, method_id2remark_name, data_remark_name2id, method_remark_name2id
from pyerm.webUI import PYERM_HOME

def record():
    title()
    if st.session_state.db_path.endswith('.db'):
        if os.path.exists(st.session_state.db_path):
            db = Database(st.session_state.db_path, output_info=False)
        else:
            db = None
        cols = st.columns(3)
        with cols[0]:
            # task select
            task_select(db=db)
        
        with cols[1]:
            # method select
            method_select(db=db, task=st.session_state.record_task)

        with cols[2]:
            # data select
            data_select(db=db, task=st.session_state.record_task)
        
        cols = st.columns(2)
        with cols[0]:
            if st.session_state.record_method:
                method_remark = set_method_param(db=db, method=st.session_state.record_method)

        with cols[1]:
            if st.session_state.record_data:
                data_remark = set_data_param(db=db, data=st.session_state.record_data)

        if st.session_state.record_task is not None and st.session_state.record_method is not None and st.session_state.record_data is not None:
            set_experiment_info()

        if st.session_state.record_experiment_info is not None and st.session_state.record_experiment_info['status'] == st.session_state.lm["record.status_over"]:
            set_experiment_result(db, task=st.session_state.record_task)

        st.sidebar.write(st.session_state.lm["record.sidebar_title"])
        st.sidebar.write(st.session_state.lm["record.sidebar_task"], st.session_state.record_task if st.session_state.record_task else st.session_state.lm["record.not_setted"])
        st.sidebar.write(st.session_state.lm["record.sidebar_method"], st.session_state.record_method if st.session_state.record_method else st.session_state.lm["record.not_setted"])
        st.sidebar.write(st.session_state.lm["record.sidebar_data"], st.session_state.record_data if st.session_state.record_data else st.session_state.lm["record.not_setted"])
        st.sidebar.write(st.session_state.lm["record.sidebar_method_title"])
        if st.session_state.record_method_params is not None:
            if st.session_state.record_method_params is not -1:
                st.sidebar.dataframe(st.session_state.record_method_params, use_container_width=True)
            else:
                st.sidebar.write(st.session_state.lm["record.no_setting"])
        else:
            st.sidebar.write(st.session_state.lm["record.not_setted"])

        st.sidebar.write(st.session_state.lm["record.sidebar_data_title"])
        if st.session_state.record_data_params is not None:
            if st.session_state.record_data_params is not -1:
                st.sidebar.dataframe(st.session_state.record_data_params, use_container_width=True)
            else:
                st.sidebar.write(st.session_state.lm["record.no_setting"])
        else:
            st.sidebar.write(st.session_state.lm["record.not_setted"])

        st.sidebar.write(st.session_state.lm["record.sidebar_experiment_info_title"])
        if st.session_state.record_experiment_info is not None:
            show_experiment_info()
        else:
            st.sidebar.write(st.session_state.lm["record.not_setted"])

        if st.session_state.record_experiment_info is not None and st.session_state.record_experiment_info['status'] == st.session_state.lm["record.status_over"]:
            st.sidebar.write(st.session_state.lm["record.sidebar_experiment_result_title"])
            if st.session_state.record_result_scores is not None:
                show_experiment_result()
            else:
                st.sidebar.write(st.session_state.lm["record.not_setted"])

        if st.sidebar.button(st.session_state.lm["record.add_experiment_button"]):
            del(db)
            if st.session_state.record_task is None or st.session_state.record_method is None \
                    or st.session_state.record_data is None or st.session_state.record_method_params is None \
                    or st.session_state.record_data_params is None or st.session_state.record_experiment_info is None:
                st.sidebar.error(st.session_state.lm["record.need_full_info"])
            elif st.session_state.record_experiment_info["status"] == st.session_state.lm["record.status_over"] and st.session_state.record_result_scores is None:
                st.sidebar.error(st.session_state.lm["record.need_result_info"])
            else:
                exp = Experiment(st.session_state.db_path)
                try:
                    exp.task_init(st.session_state.record_task)
                    if st.session_state.record_method_params != -1:
                        method_param_dict = st.session_state.record_method_params.to_dict(orient='records')[0]
                    else:
                        method_param_dict = {}
                    exp.method_init(st.session_state.record_method, method_param_dict, remark=method_remark)
                    if st.session_state.record_data_params != -1:
                        data_param_dict = st.session_state.record_data_params.to_dict(orient='records')[0]
                    else:
                        data_param_dict = {}
                    exp.data_init(st.session_state.record_data, data_param_dict, remark=data_remark)
                    end_time = st.session_state.record_experiment_info.pop("end_time")
                    status = st.session_state.record_experiment_info.pop("status")
                    failed_reason = st.session_state.record_experiment_info.pop("failed_reason")
                    usefule_time_cost = st.session_state.record_experiment_info.pop("useful_time_cost")
                    exp.experiment_start(**st.session_state.record_experiment_info)
                    if status == st.session_state.lm["record.status_over"]:
                        exp.experiment_over(st.session_state.record_result_scores.to_dict(orient='records')[0], st.session_state.record_result_imgs, end_time=end_time, useful_time_cost=usefule_time_cost)
                    elif status == st.session_state.lm["record.status_failed"]:
                        exp.experiment_failed(end_time=end_time, error_info=failed_reason)
                    st.session_state.record_experiment_info["end_time"] = end_time
                    st.session_state.record_experiment_info["status"] = status
                    st.session_state.record_experiment_info["failed_reason"] = failed_reason
                    st.session_state.record_experiment_info["useful_time_cost"] = usefule_time_cost
                    st.sidebar.success(st.session_state.lm["record.add_experiment_success"])
                    st.session_state.record_result_scores = None
                    st.session_state.record_result_imgs = {}
                except Exception as e:
                    st.sidebar.error(st.session_state.lm["record.add_experiment_failed"] + str(e))
                
    st.sidebar.write("---")
    if st.sidebar.button(st.session_state.lm["app.refresh"], key='refresh', use_container_width=True):
        st.rerun()
        
def task_select(db: Database):
    task = None
    st.write(st.session_state.lm["record.task_select.title"])
    try:
        tasks = pd.read_sql_query("SELECT DISTINCT task FROM experiment_list", db.conn)
        task = st.selectbox(st.session_state.lm["record.task_select.task_select"], tasks)
    except Exception as e:
        st.write(st.session_state.lm["record.task_select.task_empty"])
    if st.checkbox(st.session_state.lm["record.task_select.add_new_task_checkbox"]):
        task = st.text_input(st.session_state.lm["record.task_select.add_new_task_input"], key="new_task")
    if st.button(st.session_state.lm["record.task_select.task_ok"], key="task_ok"):
        if task is None:
            st.error(st.session_state.lm["record.task_select.task_empty_error"])
        else:
            st.session_state.record_task = task

def method_select(db: Database, task: str):
    method = None
    st.write(st.session_state.lm["record.method_select.title"])
    try:
        methods = pd.read_sql_query(f"SELECT DISTINCT method FROM experiment_list WHERE task = '{task}'", db.conn)
        method = st.selectbox(st.session_state.lm["record.method_select.method_select"], methods)
    except Exception as e:
        st.write(st.session_state.lm["record.method_select.method_empty"])
    if st.checkbox(st.session_state.lm["record.method_select.add_new_method_checkbox"]):
        method = st.text_input(st.session_state.lm["record.method_select.add_new_method_input"], key="new_method")
    if st.button(st.session_state.lm["record.method_select.method_ok"], key="method_ok"):
        if method is None:
            st.error(st.session_state.lm["record.method_select.method_empty_error"])
        else:
            st.session_state.record_method = method

def set_method_param(db: Database, method: str):
    remark = None 
    st.write(st.session_state.lm["record.set_method_param.title"])
    table_name = f"method_{method}"
    if db is not None and table_name in db.table_names:
        st.write(st.session_state.lm["record.set_method_param.param_table_found"])
        cur_method_params = pd.read_sql_query(f"SELECT * FROM {table_name}", db.conn)
        remarks = [method_id2remark_name(db, method, method_id) for method_id in cur_method_params["method_id"]]
        selected_remark = st.selectbox(st.session_state.lm["record.set_method_param.cur_param_select"], remarks)
        selected_param = cur_method_params[cur_method_params["method_id"] == method_remark_name2id(db, method, selected_remark)]
        selected_param = selected_param.drop(columns=["method_id", "remark"])
        selected_param.index = [st.session_state.lm["record.set_method_param.param_table_row_name"]]
        if st.checkbox(st.session_state.lm["record.set_method_param.add_new_param_checkbox"], key="add_new_method_param"):
            st.write(st.session_state.lm["record.set_method_param.add_new_param_notice"])
            new_param_num = st.number_input(st.session_state.lm["record.set_method_param.new_param_num"], min_value=1, value=1, key="new_method_param_num")
            for i in range(new_param_num):
                new_param = st.text_input(st.session_state.lm["record.set_method_param.new_param_name_input"].format(PARAM_INDEX=i+1), key=f"new_method_param_name_{i}", value=f"param_{i+1}")
                data_type_i = st.selectbox(st.session_state.lm["record.set_method_param.new_param_type_input"].format(PARAM_INDEX=i+1), ["int", "float", "str", "bool"], key=f"new_method_param_type_{i}")
                if new_param in selected_param.columns:
                    st.error(st.session_state.lm["record.set_method_param.new_param_name_repeat_error"])
                    break
                new_param = pd.DataFrame({new_param: [0 if data_type_i != "str" else None]},
                                          index=[st.session_state.lm["record.set_method_param.param_table_row_name"]], dtype=data_type_i)
                selected_param = pd.concat([selected_param, new_param], axis=1)
        st.write(st.session_state.lm["record.set_method_param.table_edit_hint"])
        params = st.data_editor(selected_param, use_container_width=True, key="new_method_param")
        if st.checkbox(st.session_state.lm["record.set_method_param.remark_param_checkbox"], key="remark_method_param"):
            st.write(st.session_state.lm["record.set_method_param.remark_param_notice"])
            remark = st.text_input(st.session_state.lm["record.set_method_param.remark_param_input"], key="remark_method_param_input")
            params.index = [remark]
        if st.button(st.session_state.lm["record.set_method_param.param_ok"], key="param_method_ok"):
            st.session_state.record_method_params = params
    else:
        params = -1
        st.write(st.session_state.lm["record.set_method_param.param_table_not_found"])
        if st.checkbox(st.session_state.lm["record.set_method_param.create_new_param_table"]):
            st.write(st.session_state.lm["record.set_method_param.add_new_param_notice"])
            new_param_num = st.number_input(st.session_state.lm["record.set_method_param.new_param_num"], min_value=1, value=1, key="new_method_param_num")
            new_param = pd.DataFrame()
            for i in range(new_param_num):
                new_param_name = st.text_input(st.session_state.lm["record.set_method_param.new_param_name_input"].format(PARAM_INDEX=i+1), key=f"new_method_param_name_{i}", value=f"param_{i+1}")
                data_type_i = st.selectbox(st.session_state.lm["record.set_method_param.new_param_type_input"].format(PARAM_INDEX=i+1), ["int", "float", "str", "bool"], key=f"new_method_param_type_{i}")
                if new_param_name in new_param.columns:
                    st.error(st.session_state.lm["record.set_method_param.new_param_name_repeat_error"])
                    break
                new_param = pd.concat([new_param, pd.DataFrame({new_param_name: [0 if data_type_i != "str" else None]},
                                                                index=[st.session_state.lm["record.set_method_param.param_table_row_name"]], dtype=data_type_i)], axis=1)
            st.write(st.session_state.lm["record.set_method_param.table_edit_hint"])
            params = st.data_editor(new_param, use_container_width=True, key="new_method_param")
            if st.checkbox(st.session_state.lm["record.set_method_param.remark_param_checkbox"], key="remark_method_param"):
                st.write(st.session_state.lm["record.set_method_param.remark_param_notice"])
                remark = st.text_input(st.session_state.lm["record.set_method_param.remark_param_input"], key="remark_method_param_input")
                params.index = [remark]
        if st.button(st.session_state.lm["record.set_method_param.param_ok"], key="param_method_ok"):
            st.session_state.record_method_params = params

    return remark

def data_select(db: Database, task: str):
    data = None
    st.write(st.session_state.lm["record.data_select.title"])
    try:
        datas = pd.read_sql_query(f"SELECT DISTINCT data FROM experiment_list WHERE task = '{task}'", db.conn)
        data = st.selectbox(st.session_state.lm["record.data_select.data_select"], datas)
    except Exception as e:
        st.write(st.session_state.lm["record.data_select.data_empty"])
    if st.checkbox(st.session_state.lm["record.data_select.add_new_data_checkbox"]):
        data = st.text_input(st.session_state.lm["record.data_select.add_new_data_input"], key="new_data")
    if st.button(st.session_state.lm["record.data_select.data_ok"], key="data_ok"):
        if data is None:
            st.error(st.session_state.lm["record.data_select.data_empty_error"])
        else:
            st.session_state.record_data = data

def set_data_param(db: Database, data: str):
    remark = None 
    st.write(st.session_state.lm["record.set_data_param.title"])
    table_name = f"data_{data}"
    if db is not None and table_name in db.table_names:
        st.write(st.session_state.lm["record.set_data_param.param_table_found"])
        cur_data_params = pd.read_sql_query(f"SELECT * FROM {table_name}", db.conn)
        remarks = [data_id2remark_name(db, data, data_id) for data_id in cur_data_params["data_id"]]
        selected_remark = st.selectbox(st.session_state.lm["record.set_data_param.cur_param_select"], remarks)
        selected_param = cur_data_params[cur_data_params["data_id"] == data_remark_name2id(db, data, selected_remark)]
        selected_param = selected_param.drop(columns=["data_id", "remark"])
        selected_param.index = [st.session_state.lm["record.set_data_param.param_table_row_name"]]
        if st.checkbox(st.session_state.lm["record.set_data_param.add_new_param_checkbox"], key="add_new_data_param"):
            st.write(st.session_state.lm["record.set_data_param.add_new_param_notice"])
            new_param_num = st.number_input(st.session_state.lm["record.set_data_param.new_param_num"], min_value=1, value=1, key="new_data_param_num")
            for i in range(new_param_num):
                new_param = st.text_input(st.session_state.lm["record.set_data_param.new_param_name_input"].format(PARAM_INDEX=i+1), key=f"new_data_param_name_{i}", value=f"param_{i+1}")
                data_type_i = st.selectbox(st.session_state.lm["record.set_data_param.new_param_type_input"].format(PARAM_INDEX=i+1), ["int", "float", "str", "bool"], key=f"new_data_param_type_{i}")
                if new_param in selected_param.columns:
                    st.error(st.session_state.lm["record.set_data_param.new_param_name_repeat_error"])
                    break
                new_param = pd.DataFrame({new_param: [0 if data_type_i != "str" else None]}, index=["参数"], dtype=data_type_i)
                selected_param = pd.concat([selected_param, new_param], axis=1)
        st.write(st.session_state.lm["record.set_data_param.table_edit_hint"])
        params = st.data_editor(selected_param, use_container_width=True, key="new_data_param")
        if st.checkbox(st.session_state.lm["record.set_data_param.remark_param_checkbox"], key="remark_data_param"):
            st.write(st.session_state.lm["record.set_data_param.remark_param_notice"])
            remark = st.text_input(st.session_state.lm["record.set_data_param.remark_param_input"], key="remark_data_param_input")
            params.index = [remark]
        if st.button(st.session_state.lm["record.set_data_param.param_ok"], key="param_data_ok"):
            st.session_state.record_data_params = params
    else:
        params = -1
        st.write(st.session_state.lm["record.set_data_param.param_table_not_found"])
        if st.checkbox(st.session_state.lm["record.set_data_param.create_new_param_table"]):
            st.write(st.session_state.lm["record.set_data_param.add_new_param_notice"])
            new_param_num = st.number_input(st.session_state.lm["record.set_data_param.new_param_num"], min_value=1, value=1, key="new_data_param_num")
            new_param = pd.DataFrame()
            for i in range(new_param_num):
                new_param_name = st.text_input(st.session_state.lm["record.set_data_param.new_param_name_input"].format(PARAM_INDEX=i+1), key=f"new_data_param_name_{i}", value=f"param_{i+1}")
                data_type_i = st.selectbox(st.session_state.lm["record.set_data_param.new_param_type_input"].format(PARAM_INDEX=i+1), ["int", "float", "str", "bool"], key=f"new_data_param_type_{i}")
                if new_param_name in new_param.columns:
                    st.error(st.session_state.lm["record.set_data_param.new_param_name_repeat_error"])
                    break
                new_param = pd.concat([new_param, pd.DataFrame({new_param_name: [0 if data_type_i != "str" else None]}, index=["参数"], dtype=data_type_i)], axis=1)
            st.write(st.session_state.lm["record.set_data_param.table_edit_hint"])
            params = st.data_editor(new_param, use_container_width=True, key="new_data_param")
            if st.checkbox(st.session_state.lm["record.set_data_param.remark_param_checkbox"], key="remark_data_param"):
                st.write(st.session_state.lm["record.set_data_param.remark_param_notice"])
                remark = st.text_input(st.session_state.lm["record.set_data_param.remark_param_input"], key="remark_data_param_input")
                params.index = [remark]
        if st.button(st.session_state.lm["record.set_data_param.param_ok"], key="param_data_ok"):
            st.session_state.record_data_params = params
    
    return remark

def set_experiment_info():
    st.write(st.session_state.lm["record.set_experiment_info.title"])
    desc = st.text_area(st.session_state.lm["record.set_experiment_info.experiment_description_input"], key="exp_desc")
    tags = st.text_input(st.session_state.lm["record.set_experiment_info.experiment_tags_input"], key="exp_tags")
    experimenters = st.text_input(st.session_state.lm["record.set_experiment_info.experimenters_input"], key="exp_experimenters")
    cols = st.columns(2)
    with cols[0]:
        start_date = st.date_input(st.session_state.lm["record.set_experiment_info.start_date_input"], key="exp_start_date", value=None)
        end_date = st.date_input(st.session_state.lm["record.set_experiment_info.end_date_input"], key="exp_end_date", value=None)
    with cols[1]:
        start_time = st.time_input(st.session_state.lm["record.set_experiment_info.start_time_input"], key="exp_start_time", value=None) 
        end_time = st.time_input(st.session_state.lm["record.set_experiment_info.end_time_input"], key="exp_end_time", value=None)
    useful_time_cost = st.number_input(st.session_state.lm["record.set_experiment_info.useful_time_input"], key="exp_useful_time_cost", value=None)
    status = st.selectbox(st.session_state.lm["record.set_experiment_info.status_select"],
                            [st.session_state.lm["record.status_over"], st.session_state.lm["record.status_failed"]],
                            key="exp_status")
    if status == st.session_state.lm["record.status_failed"]:
        failed_reason = st.text_area(st.session_state.lm["record.set_experiment_info.failed_reason_input"], key="exp_failed_reason")
    else:
        failed_reason = None
    if st.checkbox(st.session_state.lm["record.set_experiment_info.add_remark_checkbox"]):
        remark = st.text_input(st.session_state.lm["record.set_experiment_info.add_remark_input"], key="exp_remark")
    else:
        remark = None
    if st.button(st.session_state.lm["record.set_experiment_info.experiment_ok"], key="exp_ok"):
        st.session_state.record_experiment_info = {
            "description": desc,
            "tags": tags,
            "experimenters": experimenters,
            "start_time": datetime.datetime.combine(start_date, start_time).timestamp() if start_date and start_time else "",
            "end_time": datetime.datetime.combine(end_date, end_time).timestamp() if end_date and end_time else "",
            "useful_time_cost": useful_time_cost,
            "status": status,
            "failed_reason": failed_reason,
            "remark": remark
        }
    
def show_experiment_info():
    remark = st.session_state.record_experiment_info["remark"] if st.session_state.record_experiment_info["remark"] else ""
    desp = st.session_state.lm["record.show_experiment_info.description1"].format(TASK=st.session_state.record_task, REMARK=remark, METHOD=st.session_state.record_method, DATA=st.session_state.record_data)
    if st.session_state.record_experiment_info["experimenters"]:
        desp += st.session_state.lm["record.show_experiment_info.description2"].format(EXPERIMENTERS=st.session_state.record_experiment_info["experimenters"])
    if st.session_state.record_experiment_info["start_time"]:
        desp += st.session_state.lm["record.show_experiment_info.description3"].format(START_TIME=datetime.datetime.fromtimestamp(st.session_state.record_experiment_info["start_time"]).strftime("%Y-%m-%d %H:%M:%S"))
    if st.session_state.record_experiment_info["end_time"]:
        desp += st.session_state.lm["record.show_experiment_info.description4"].format(END_TIME=datetime.datetime.fromtimestamp(st.session_state.record_experiment_info["end_time"]).strftime("%Y-%m-%d %H:%M:%S"))
    if st.session_state.record_experiment_info["useful_time_cost"]:
        desp += st.session_state.lm["record.show_experiment_info.description5"].format(USEFUL_TIME_COST=st.session_state.record_experiment_info["useful_time_cost"])
    st.sidebar.write(desp)
    if st.session_state.record_experiment_info["status"] == st.session_state.lm["record.status_failed"]:
        st.sidebar.write(st.session_state.lm["record.show_experiment_info.failed_text"])
        st.sidebar.code(st.session_state.record_experiment_info["failed_reason"])
    elif st.session_state.record_experiment_info["status"] == st.session_state.lm["record.status_over"]:
        st.sidebar.write(st.session_state.lm["record.show_experiment_info.finished_text"])
    if st.session_state.record_experiment_info["description"]:
        st.sidebar.write(st.session_state.lm["record.show_experiment_info.experiment_desc"].format(DESCRIPTION=st.session_state.record_experiment_info["description"]))
    if st.session_state.record_experiment_info["experimenters"]:
        st.sidebar.write(st.session_state.lm["record.show_experiment_info.experimenters"].format(EXPERIMENTERS=st.session_state.record_experiment_info["experimenters"]))
    if st.session_state.record_experiment_info["tags"]:
        st.sidebar.write(st.session_state.lm["record.show_experiment_info.experiment_tags"].format(TAGS=st.session_state.record_experiment_info["tags"]))

def set_experiment_result(db:Database, task):
    st.write(st.session_state.lm["record.set_experiment_result.title"])
    task_table_name = f"result_{task}"
    if db is None or task_table_name not in db.table_names:
        init_score_name = st.text_input(st.session_state.lm["record.set_experiment_result.init_score_name_input"], key="init_score_name", value="score_0")
        score = pd.DataFrame(columns=[init_score_name])
        score_columns = score.columns
    else:
        result_table = db[f"result_{task}"]
        score_columns = [col for col in result_table.columns if not col.startswith("image_") and not col == "experiment_id"]
        score = pd.DataFrame(columns=score_columns)
    for col in score_columns:
        score[col] = [0]
    score.index = [st.session_state.lm["record.set_experiment_result.score_table_row_name"]]
    cols = st.columns(2)
    with cols[0]:
        st.write(st.session_state.lm["record.set_experiment_result.score_table_title"])
        if st.checkbox(st.session_state.lm["record.set_experiment_result.add_new_score_checkbox"]):
            st.write(st.session_state.lm["record.set_experiment_result.add_new_score_notice"])
            new_score_num = st.number_input(st.session_state.lm["record.set_experiment_result.new_score_num"], min_value=1, value=1, key="new_score_num")
            for i in range(new_score_num):
                new_score = st.text_input(st.session_state.lm["record.set_experiment_result.new_score_name_input"].format(SCORE_INDEX=i+1), key=f"new_score_name_{i}", value=f"score_{i+1}")
                if new_score in score.columns:
                    st.error(st.session_state.lm["record.set_experiment_result.new_score_name_repeat_error"])
                    break
                score = pd.concat([score, pd.DataFrame({new_score: [0]}, index=[st.session_state.lm["record.set_experiment_result.score_table_row_name"]])], axis=1)
        score = st.data_editor(score, use_container_width=True)
        for col in score.columns:
            score[col] = score[col].astype(float)
        if st.button(st.session_state.lm["record.set_experiment_result.result_ok"], key="exp_score_ok"):
            st.session_state.record_result_scores = score
    with cols[1]:
        st.write(st.session_state.lm["record.set_experiment_result.add_img_title"])
        imgs = st.file_uploader(st.session_state.lm["record.set_experiment_result.img_uploader"], type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="exp_imgs")
        img_dict = {}
        for img in imgs:
            img_dict[img.name] = Image.open(io.BytesIO(img.read()))
        if st.button(st.session_state.lm["record.set_experiment_result.result_ok"], key="exp_img_ok"):
            st.session_state.record_result_imgs = img_dict
            
def show_experiment_result():
    if st.session_state.record_result_scores is not None:
        st.sidebar.write(st.session_state.lm["record.show_experiment_result.sidebar_scores_title"])
        st.sidebar.dataframe(st.session_state.record_result_scores, use_container_width=True)
        # st.sidebar.write(st.session_state.record_result_scores.to_dict(orient='records')[0])
    if st.session_state.record_result_imgs is not None:
        st.sidebar.write(st.session_state.lm["record.show_experiment_result.sidebar_imgs_title"])
        # st.sidebar.write(st.session_state.record_result_imgs)
        img = st.sidebar.selectbox(st.session_state.lm["record.show_experiment_result.sidebar_img_select"], list(st.session_state.record_result_imgs.keys()))
        if img:
            st.sidebar.image(st.session_state.record_result_imgs[img], use_column_width=True)

def title():
    st.title(st.session_state.lm["record.title"])
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(st.session_state.lm["app.dataset_load_success_text"].format(DB_PATH=st.session_state.db_path))
    else:
        st.write(st.session_state.lm["app.dataset_load_failed_text"])

    