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
import numpy as np
import pandas as pd
import streamlit as st
import os
from PIL import Image
import io
from datetime import datetime
from time import time

from pyerm.database.dbbase import Database
from pyerm.database.utils import split_result_info, get_result_statistics, experiment_remark_name2id
from pyerm.webUI import PYERM_HOME

def details():
    title()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        db = Database(st.session_state.db_path, output_info=False)
        experiment_table = db['experiment_list']
        max_id, min_id = experiment_table.select('MAX(id)', 'MIN(id)')[0]
        
        if st.session_state.cur_detail_id is None:
            cur_id= detect_experiment_id(db)
        else:
            cur_id = st.session_state.cur_detail_id
        if cur_id is None:
            st.write(st.session_state.lm["details.no_experiment_found_text"])
        else:
            st.sidebar.markdown(st.session_state.lm["details.sidebar_choose_experiment_title"])
            cur_id_last = cur_id
            cur_remark_name = experiment_table.select("remark", where=f'id={cur_id}')
            cur_remark_name = cur_remark_name[0][0] if cur_remark_name else None
            cur_id = st.sidebar.text_input(st.session_state.lm["details.sidebar_choose_experiment_input"], key='input_exp_id', value=cur_id if cur_remark_name is None else cur_remark_name)
            if cur_id.isdigit():
                cur_id = int(cur_id)
            else:
                cur_id = experiment_remark_name2id(db, cur_id)
            st.session_state.cur_detail_id = cur_id
            if cur_id_last != cur_id:
                st.session_state.cur_detail_img_id = 0
            if st.sidebar.checkbox(st.session_state.lm["details.sidebar_only_show_remark_checkbox"], key='only_remark'):
                only_remark = True
            else:
                only_remark = False
            cols_sidebar = st.sidebar.columns(2)
            cur_id_last = cur_id 
            with cols_sidebar[0]:
                if st.button(st.session_state.lm["details.sidebar_last_experiment_button"], disabled=cur_id <= min_id):
                    cur_id  = detect_experiment_id(db, False, only_remark=only_remark)
                if st.button(st.session_state.lm["details.sidebar_the_first_experiment_button"]):
                    st.session_state.cur_detail_id = min_id
                    st.rerun()
            with cols_sidebar[1]:
                if st.button(st.session_state.lm["details.sidebar_next_experiment_button"], disabled=cur_id >= max_id):
                    cur_id = detect_experiment_id(db, True, only_remark=only_remark)
                if st.button(st.session_state.lm["details.sidebar_the_last_experiment_button"]):
                    st.session_state.cur_detail_id = max_id
                    st.rerun()
            if cur_id_last != cur_id:
                st.rerun()
            

        if experiment_table.select(where=f'id={cur_id}') == []:
            st.markdown(st.session_state.lm["details.experiment_information_title"])
            if cur_id == -1:
                cur_id = 'Unknown'
            st.markdown(st.session_state.lm["details.experiment_information_id"].format(CUR_ID=cur_id))
            st.write(st.session_state.lm["details.experiment_not_exist_text"].format(CUR_ID=cur_id))
        else:
            st.markdown(st.session_state.lm["details.experiment_information_title"])
            cur_remark_name = experiment_table.select(where=f'id={cur_id}')[0][-2]
            st.markdown(st.session_state.lm["details.experiment_information_id"].format(CUR_ID=cur_id) + (f"({cur_remark_name})" if cur_remark_name else ''))
            
            basic_info, method_info, data_info, result_info = detect_experiment_info(db)
            basic_information(basic_info)
            
            remark_cur_experiment(db)
            
            st.write('---')
            cols = st.columns(2)
            with cols[0]:
                st.write(st.session_state.lm["details.experiment_result_title"])
                if result_info is not None:
                    result_info, image_dict = split_result_info(result_info)
                    result_info, num_same_setting_records = calculate_result_statistics(db, basic_info, result_info)
                    selected_img = st.selectbox(st.session_state.lm["details.experiment_result_image_select"], list(image_dict.keys()), key='select_img')
                    if selected_img:
                        st.image(Image.open(io.BytesIO(image_dict[selected_img])))
                        with io.BytesIO(image_dict[selected_img]) as buf:
                            img_data = buf.read()
                        st.download_button(
                            label=st.session_state.lm["details.experiment_result_image_download"].format(SELECTED_IMG=selected_img),
                            data=img_data,
                            file_name=f"{selected_img}.png",
                            mime="image/png"
                        )
                    else:
                        st.write(st.session_state.lm["details.experiment_result_image_not_exist"].format(CUR_ID=cur_id))
                    st.write(st.session_state.lm["details.experiment_result_scores_title"])
                    st.write(result_info)
                    st.write(st.session_state.lm["details.experiment_result_scores_notice"].format(NUM_SAME_SETTING_RECORDS=num_same_setting_records))
                else:
                    st.write(st.session_state.lm["details.experiment_result_not_exists"])
            with cols[1]:
                st.write(st.session_state.lm["details.experiment_method_param_title"])
                if method_info is not None: 
                    if len(method_info) == 0:
                        st.write(st.session_state.lm["details.experiment_method_param_not_exist"])
                    else:
                        method_remark_name = method_info['remark'][0]
                        if method_remark_name:
                            st.write(st.session_state.lm["details.experiment_method_remark"].format(METHOD_REMARK_NAME=method_remark_name))
                        method_info.drop(columns=['remark'], inplace=True)
                        method_info.index = [st.session_state.lm["details.experiment_method_index"]]
                        st.dataframe(method_info.astype(str).transpose(), use_container_width=True)
                else:
                    st.write(st.session_state.lm["details.experiment_method_no_param"])
                    
                st.write('---')
                st.write(st.session_state.lm["details.experiment_data_param_title"])
                if data_info is not None:
                    if len(data_info) == 0:
                        st.write(st.session_state.lm["details.experiment_data_param_not_exist"])
                    else:
                        data_remark_name = data_info['remark'][0]
                        if data_remark_name:
                            st.write(st.session_state.lm["details.experiment_data_remark"].format(DATA_REMARK_NAME=data_remark_name))
                        data_info.drop(columns=['remark'], inplace=True)
                        data_info.index = [st.session_state.lm["details.experiment_data_index"]]
                        st.dataframe(data_info.astype(str).transpose(), use_container_width=True)
                else:
                    st.write(st.session_state.lm["details.experiment_data_no_param"])
            
            if f'detail_{cur_id}' in db.table_names:
                st.write('---')
                st.markdown(st.session_state.lm["details.experiment_detail_title"])
                detail_table = db[f'detail_{cur_id}']
                detail_columns = detail_table.columns
                detail_data = detail_table.select()
                detail_df = pd.DataFrame(detail_data, columns=detail_columns)
                st.write(detail_df)
            
                
            st.write('---')
            st.markdown(st.session_state.lm["details.experiment_delete_title"])
            st.markdown(st.session_state.lm["details.experiment_delete_warn"])
            if st.checkbox(st.session_state.lm["details.experiment_delete_checkbox"], value=False):
                if st.button(st.session_state.lm["details.experiment_delete_confirm_button"]):
                    delete_current_experiment(db)
    if st.sidebar.button(st.session_state.lm["app.refresh"], key='refresh'):
        st.rerun()

def basic_information(basic_info:pd.DataFrame):
    id = basic_info['id'][0]
    description = basic_info['description'][0]
    method = basic_info['method'][0]
    data = basic_info['data'][0]
    task = basic_info['task'][0]
    tags = basic_info['tags'][0]
    experimenters = basic_info['experimenters'][0]
    start_time = basic_info['start_time'][0]
    end_time = basic_info['end_time'][0]
    useful_time_cost = basic_info['useful_time_cost'][0]
    total_time_cost = basic_info['total_time_cost'][0]
    status = basic_info['status'][0]
    failed_reason = basic_info['failed_reason'][0]
    st.write(st.session_state.lm["details.basic_information.task"].format(TASK=task))
    st.write(st.session_state.lm["details.basic_information.method"].format(METHOD=method)) 
    st.write(st.session_state.lm["details.basic_information.data"].format(DATA=data)) 
    desp = st.session_state.lm["details.basic_information.desp_part1"].format(ID=id, TASK=task, METHOD=method, DATA=data)
    if experimenters:
        desp += st.session_state.lm["details.basic_information.desp_part2"].format(EXPERIMENTERS=experimenters)
    if start_time:
        desp += st.session_state.lm["details.basic_information.desp_part3"].format(START_TIME=start_time)
    if end_time:
        desp += st.session_state.lm["details.basic_information.desp_part4"].format(END_TIME=end_time)
    st.write(desp)
    if status == 'failed':
        st.write(st.session_state.lm["details.basic_information.failed_text"])
        st.code(f"{failed_reason}")
    elif status == 'finished':
        st.write(st.session_state.lm["details.basic_information.finished_text1"].format(TOTAL_TIME_COST=total_time_cost) + 
                 st.session_state.lm["details.basic_information.finished_text2"].format(USEFUL_TIME_COST=useful_time_cost) if useful_time_cost else 
                 st.session_state.lm["details.basic_information.finished_text3"])
    else:
        time_cost = time() - datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp()
        st.write(st.session_state.lm["details.basic_information.running_text"].format(TIME_COST=time_cost))
    st.write('')
    if description:
        st.write(st.session_state.lm["details.basic_information.desp"].format(DESCRIPTION=description))
    if experimenters:
        st.write(st.session_state.lm["details.basic_information.experimenters"].format(EXPERIMENTERS=experimenters))
    if tags:
        st.write(st.session_state.lm["details.basic_information.tags"].format(TAGS=tags))

def calculate_result_statistics(db, basic_info: pd.DataFrame, result_info: pd.DataFrame):
    task = basic_info['task'][0]
    method = basic_info['method'][0]
    method_id = basic_info['method_id'][0]
    data = basic_info['data'][0]
    data_id = basic_info['data_id'][0]
    
    statistics, same_setting_ids = get_result_statistics(db, task, method, method_id, data, data_id)
    num_same_setting = len(same_setting_ids)
    
    result_info.index = ['Cur']
    result_info = pd.concat([result_info, statistics], axis=0)
    
    return result_info, num_same_setting
    
def detect_experiment_id(db, next_flag=True, only_remark=False):
    experiment_table = db['experiment_list']
    if st.session_state.cur_detail_id is None:
        basic_info = experiment_table.select(other='ORDER BY id DESC LIMIT 1')
        if len(basic_info) == 0:
            return None
        # st.write(basic_info)
    elif only_remark:
        basic_info = experiment_table.select(where=f'id{">" if next_flag else "<"}{st.session_state.cur_detail_id} AND remark is not NULL', other=f'ORDER BY id {"ASC" if next_flag else "DESC"} LIMIT 1')
    else:
        basic_info = experiment_table.select(where=f'id{">" if next_flag else "<"}{st.session_state.cur_detail_id}', other=f'ORDER BY id {"ASC" if next_flag else "DESC"} LIMIT 1')
    try:
        st.session_state.cur_detail_id = basic_info[0][0]
        st.session_state.cur_detail_img_id = 0
        return st.session_state.cur_detail_id
    except:
        return st.session_state.cur_detail_id
        
def detect_experiment_info(db):
    experiment_table = db['experiment_list']
    basic_info = experiment_table.select(where=f'id={st.session_state.cur_detail_id}')
    basic_columns = experiment_table.columns
    method = basic_info[0][2]
    method_id = basic_info[0][3]
    method_info = None
    data = basic_info[0][4]
    data_id = basic_info[0][5]
    data_info = None
    result_info = None
    task = basic_info[0][6]
    if method_id != -1:
        method_table = db[f'method_{method}']
        method_info = method_table.select(where=f'method_id={method_id}')
        method_columns = method_table.columns
        method_info = pd.DataFrame(method_info, columns=method_columns)
    if data_id != -1:
        data_table = db[f'data_{data}']
        data_info = data_table.select(where=f'data_id={data_id}')
        data_columns = data_table.columns
        data_info = pd.DataFrame(data_info, columns=data_columns)
    if basic_info[0][13] == 'finished':
        result_table = db[f'result_{task}']
        result_info = result_table.select(where=f'experiment_id={st.session_state.cur_detail_id}')
        result_columns = result_table.columns
        result_info = pd.DataFrame(result_info, columns=result_columns)
    basic_info = pd.DataFrame(basic_info, columns=basic_columns)
    return basic_info, method_info, data_info, result_info

def remark_cur_experiment(db):
    experiment_table = db['experiment_list']
    if st.checkbox(st.session_state.lm["details.remark_cur_experiment.remark_cur_experiment_checkbox"], key='remark'):
        remark = st.text_input(st.session_state.lm["details.remark_cur_experiment.remark_cur_experiment_input"], key='remark_input')

        if st.button(st.session_state.lm["details.remark_cur_experiment.remark_cur_experiment_button"], key='confirm_remark'):
            if remark.isnumeric():
                st.session_state.error_flag1 = True
            else:
                if remark == '':
                    remark = None
                try:
                    experiment_table.update(f'id={st.session_state.cur_detail_id}', remark=remark)
                    db.conn.commit()
                except:
                    st.session_state.error_flag = True

            st.rerun()
        
        if st.session_state.error_flag:
            st.write(st.session_state.lm["details.remark_cur_experiment.remark_cur_experiment_failed_repeat"])
            st.session_state.error_flag = False
        
        if st.session_state.error_flag1:
            st.write(st.session_state.lm["details.remark_cur_experiment.remark_cur_experiment_failed_number"])
            st.session_state.error_flag1 = False

def delete_current_experiment(db):
    experiment_table = db['experiment_list']
    task = experiment_table.select(where=f'id={st.session_state.cur_detail_id}')[0][6]
    experiment_table.delete(f'id={st.session_state.cur_detail_id}')
    result_table = db[f'result_{task}']
    result_table.delete(f'experiment_id={st.session_state.cur_detail_id}')
    db.conn.commit()
    st.session_state.cur_detail_id = None
    st.rerun()

def title():
    st.title(st.session_state.lm["details.title"])
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(st.session_state.lm["app.dataset_load_success_text"].format(DB_PATH=st.session_state.db_path))
    else:
        st.write(st.session_state.lm["app.dataset_load_failed_text"])
    