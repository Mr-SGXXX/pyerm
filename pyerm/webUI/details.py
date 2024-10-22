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

# Version: 0.2.8

import pandas as pd
import streamlit as st
import os
from PIL import Image
import re
import io

from pyerm.database.dbbase import Database
from pyerm.webUI import PYERM_HOME

def details():
    title()
    if st.button('Refresh', key='refresh1'):
        st.rerun()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        db = Database(st.session_state.db_path, output_info=False)
        experiment_table = db['experiment_list']
        max_id, min_id = experiment_table.select('MAX(id)', 'MIN(id)')[0]
        
        if st.session_state.cur_detail_id is None:
            cur_id = detect_experiment_id(db)
        else:
            cur_id = st.session_state.cur_detail_id
        if cur_id is None:
            st.write('No experiment found. Please make sure any experiment has been run.')
        else:
            st.sidebar.markdown('## Choose Experiment')
            cur_id_last = cur_id
            cur_id = int(st.sidebar.text_input('Experiment ID', key='input_exp_id', value=cur_id))
            st.session_state.cur_detail_id = cur_id
            if cur_id_last != cur_id:
                st.session_state.cur_detail_img_id = 0
            cols_sidebar = st.sidebar.columns(2)
            cur_id_last = cur_id 
            with cols_sidebar[0]:
                if st.button('Last\nExperiment', disabled=cur_id <= min_id):
                    cur_id = detect_experiment_id(db, False)
            with cols_sidebar[1]:
                if st.button('Next\nExperiment', disabled=cur_id >= max_id):
                    cur_id = detect_experiment_id(db)
            if cur_id_last != cur_id:
                st.rerun()
            
    
        if experiment_table.select(where=f'id={cur_id}') == []:
            st.markdown('## Experiment Information')
            st.markdown(f'### Current Experiment ID: {cur_id}')
            st.write(f'Experiment with id:{cur_id} does not exist. Please check the ID.')
        else:
            
            st.markdown('## Experiment Information')
            st.markdown(f'### Current Experiment ID: {cur_id}')
            
            basic_info, method_info, data_info, result_info = detect_experiment_info(db)
            st.write('---')
            st.write('### Basic Information:')
            st.write(basic_info)
            st.write('---')
            st.write('### Method Information:')
            if method_info is not None:
                st.write(method_info)
            else:
                st.write('No hyperparam setting used by current method.')
                
            st.write('---')
            st.write('### Data Information:')
            if data_info is not None:
                st.write(data_info)
            else:
                st.write('No hyperparam setting used by current dataset.')
            
            st.write('---')
            st.write('### Result Information:')
            if result_info is not None:
                result_info, image_dict = split_result_info(result_info)
                st.write(result_info)
                selected_img = st.selectbox('**Select Experiment Result Image**', list(image_dict.keys()), key='select_img')
                if selected_img:
                    st.image(Image.open(io.BytesIO(image_dict[selected_img])))
                else:
                    st.write(f'No image detected in experiment with id:{cur_id}.')
            else:
                st.write('No result found. Please check the status of the experiment.')
                
            st.write('---')
            st.markdown('## Delete Current Experiment')
            st.markdown('**Warning**: This operation will delete current experiment record and result, which is irreversible.')
            if st.checkbox('Delete Current Experiment'):
                if st.button('Confirm'):
                    delete_current_experiment(db)

def detect_experiment_id(db, next_flag=True):
    experiment_table = db['experiment_list']
    if st.session_state.cur_detail_id is None:
        basic_info = experiment_table.select(other='ORDER BY id DESC LIMIT 1')
        if len(basic_info) == 0:
            return None
        # st.write(basic_info)
        st.session_state.cur_detail_id = basic_info[0][0]
        st.session_state.cur_detail_img_id = 0
    else:
        basic_info = experiment_table.select(where=f'id{">" if next_flag else "<"}{st.session_state.cur_detail_id}', other=f'ORDER BY id {"ASC" if next_flag else "DESC"} LIMIT 1')
        st.session_state.cur_detail_id = basic_info[0][0]
        st.session_state.cur_detail_img_id = 0
        
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



def split_result_info(result_info):
    columns_keep = [col for col in result_info.columns if not col.startswith("image_")]
    pattern = re.compile(r'image_(\d+)$')
    image_dict = {}
    for name in result_info.columns:
        match = pattern.match(name)
        if match and not result_info[name].isnull().all():
            image_dict[result_info[f"{name}_name"][0]] = result_info[name][0]
        elif result_info[name].isnull().all():
            break
    
    return result_info[columns_keep], image_dict



def delete_current_experiment(db):
    experiment_table = db['experiment_list']
    task = experiment_table.select(where=f'id={st.session_state.cur_detail_id}')[0][6]
    experiment_table.delete(f'id={st.session_state.cur_detail_id}')
    result_table = db[f'result_{task}']
    result_table.delete(f'experiment_id={st.session_state.cur_detail_id}')
    db.conn.commit()
    st.session_state.cur_detail_id = None

def title():
    st.title(f'Experiment Details')
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(f'Database Loaded (In {st.session_state.db_path})')
    else:
        st.write('No database loaded, please load a database first.')
    