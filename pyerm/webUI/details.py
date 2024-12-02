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
            st.write('No experiment found. Please make sure any experiment has been run.')
        else:
            st.sidebar.markdown('## Choose Experiment')
            cur_id_last = cur_id
            cur_remark_name = experiment_table.select("remark", where=f'id={cur_id}')
            cur_remark_name = cur_remark_name[0][0] if cur_remark_name else None
            cur_id = st.sidebar.text_input('Experiment ID or remark name', key='input_exp_id', value=cur_id if cur_remark_name is None else cur_remark_name)
            if cur_id.isdigit():
                cur_id = int(cur_id)
            else:
                cur_id = experiment_remark_name2id(db, cur_id)
            st.session_state.cur_detail_id = cur_id
            if cur_id_last != cur_id:
                st.session_state.cur_detail_img_id = 0
            if st.sidebar.checkbox('Only Show Remarked Experiments', key='only_remark'):
                only_remark = True
            else:
                only_remark = False
            cols_sidebar = st.sidebar.columns(2)
            cur_id_last = cur_id 
            with cols_sidebar[0]:
                if st.button('Last\nExperiment', disabled=cur_id <= min_id):
                    cur_id  = detect_experiment_id(db, False, only_remark=only_remark)
                if st.button('Go to the First'):
                    st.session_state.cur_detail_id = min_id
                    st.rerun()
            with cols_sidebar[1]:
                if st.button('Next\nExperiment', disabled=cur_id >= max_id):
                    cur_id = detect_experiment_id(db, True, only_remark=only_remark)
                if st.button('Go to the Last'):
                    st.session_state.cur_detail_id = max_id
                    st.rerun()
            if cur_id_last != cur_id:
                st.rerun()
            

        if experiment_table.select(where=f'id={cur_id}') == []:
            st.markdown('## Experiment Information')
            if cur_id == -1:
                cur_id = 'Unknown'
            st.markdown(f'### Current Experiment ID: {cur_id}')
            st.write(f'Experiment with id:{cur_id} does not exist. Please check the ID.')
        else:
            st.markdown('## Experiment Information')
            cur_remark_name = experiment_table.select(where=f'id={cur_id}')[0][-2]
            st.markdown(f'### Current Experiment ID: {cur_id}' + (f"({cur_remark_name})" if cur_remark_name else ''))
            
            basic_info, method_info, data_info, result_info = detect_experiment_info(db)
            basic_information(basic_info)
            
            remark_cur_experiment(db)
            
            st.write('---')
            cols = st.columns(2)
            with cols[0]:
                st.write('### Experiment Result:')
                if result_info is not None:
                    result_info, image_dict = split_result_info(result_info)
                    result_info, num_same_setting_records = calculate_result_statistics(db, basic_info, result_info)
                    selected_img = st.selectbox('**Select Experiment Result Image**', list(image_dict.keys()), key='select_img')
                    if selected_img:
                        st.image(Image.open(io.BytesIO(image_dict[selected_img])))
                        with io.BytesIO(image_dict[selected_img]) as buf:
                            img_data = buf.read()
                        st.download_button(
                            label=f"Download {selected_img}",
                            data=img_data,
                            file_name=f"{selected_img}.png",
                            mime="image/png"
                        )
                    else:
                        st.write(f'No image detected in experiment with id:{cur_id}.')
                    st.write("**Result Scores:**")
                    st.write(result_info)
                    st.write(f"_**Notice**: The statistics are calculated based on the **{num_same_setting_records}** same setting experiments._")
                else:
                    st.write('No result found. Please check the status of the experiment.')
            with cols[1]:
                st.write('### Method Paramater Setting:')
                if method_info is not None: 
                    method_remark_name = method_info['remark'][0]
                    if method_remark_name:
                        st.write(f'_Remark Name_: **{method_remark_name}**')
                    method_info.drop(columns=['remark'], inplace=True)
                    method_info.index = [f'Current Experiment Setting']
                    st.dataframe(method_info.astype(str).transpose(), use_container_width=True)
                else:
                    st.write('No hyperparam setting used by current method.')
                    
                st.write('---')
                st.write('### Data Paramater Setting:')
                if data_info is not None:
                    data_remark_name = data_info['remark'][0]
                    if data_remark_name:
                        st.write(f'_Remark Name_: **{data_remark_name}**')
                    data_info.drop(columns=['remark'], inplace=True)
                    data_info.index = [f'Current Experiment Setting']
                    st.dataframe(data_info.astype(str).transpose(), use_container_width=True)
                else:
                    st.write('No hyperparam setting used by current dataset.')
            
            if f'detail_{cur_id}' in db.table_names:
                st.write('---')
                st.markdown('## Experiment Details Table')
                detail_table = db[f'detail_{cur_id}']
                detail_columns = detail_table.columns
                detail_data = detail_table.select()
                detail_df = pd.DataFrame(detail_data, columns=detail_columns)
                st.write(detail_df)
            
                
            st.write('---')
            st.markdown('## Delete Current Experiment')
            st.markdown('**Warning**: This operation will delete current experiment record and result, which is irreversible.')
            if st.checkbox('Delete Current Experiment', value=False):
                if st.button('Confirm'):
                    delete_current_experiment(db)
    if st.sidebar.button('Refresh', key='refresh'):
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
    st.write(f"#### Task: **{task}**") 
    st.write(f"#### Method: **{method}**") 
    st.write(f"#### Data: **{data}**") 
    desp = f"Experiment **ID:{id}** of task **{task}** with method **{method}** and data **{data}**"
    if experimenters:
        desp += f" conducted by **{experimenters}**"
    desp += f" started at **{start_time}** and ended at **{end_time}**."
    st.write(desp)
    if status == 'failed':
        st.write(f"**It failed** due to the following reasons: ")
        st.code(f"{failed_reason}")
    elif status == 'finished':
        st.write(f"**It finished successfully** with **total time cost: {total_time_cost:.2f}s**" + f" and **useful time cost: {useful_time_cost:.2f}s**." if useful_time_cost else ".")
    else:
        time_cost = time() - datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp()
        st.write(f"**It is still running**, current time cost is **{time_cost:.2f}s**.")
    st.write('')
    if description:
        st.write(f"_Experimnt Description_: **{description}**")
    if experimenters:
        st.write(f"_Experimenters_: **{experimenters}**")
    if tags:
        st.write(f"_Tags_: **{tags}**")

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
    if st.checkbox('Remark Current Experiment', key='remark'):
        remark = st.text_input("Set or change a remark name for current experiment. _Empty means delete remark name._", key='remark_input')

        if st.button('Confirm', key='confirm_remark'):
            if remark.isnumeric():
                st.write('Error: Remark name cannot be a positive number.')
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
            st.write('Error: Remark name already exists, please choose another one.')
            st.session_state.error_flag = False

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
    st.title(f'Experiment Details')
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(f'Database Loaded (In {st.session_state.db_path})')
    else:
        st.write('No database loaded, please load a database first.')
    