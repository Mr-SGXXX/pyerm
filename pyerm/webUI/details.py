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

import streamlit as st
import os

from pyerm.database.dbbase import Database
from pyerm.webUI import PYERM_HOME

def details():
    title()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        db = Database(st.session_state.db_path, output_info=False)
        experiment_list = db['experiment_list']
        max_id, min_id = experiment_list.select('MAX(id)', 'MIN(id)')[0]
        if st.session_state.cur_detail_id is None:
            detect_experiment_id(db)
        if st.session_state.cur_detail_id is None:
            st.write('No experiment found.')
        else:
            cols_top = st.columns(2)
            st.markdown(f'## Current Experiment ID: {st.session_state.cur_detail_id}')
            with cols_top[0]:
                if st.button('Previous', disabled=st.session_state.cur_detail_id == min_id):
                    detect_experiment_id(db, False)
            with cols_top[1]:
                if st.button('Next', disabled=st.session_state.cur_detail_id == max_id):
                    detect_experiment_id(db)    
            
            st.markdown('## Experiment Information')
            
            basic_info, method_info, data_info, result_info = detect_experiment_info(db)
            st.write('Basic Information:')
            st.write(basic_info[0])
            if method_info is not None:
                st.write('Method Information:')
                st.write(method_info[0])
            if data_info is not None:
                st.write('Data Information:')
                st.write(data_info[0])
            if result_info is not None:
                st.write('Result Information:')
                st.write(result_info[0])
                
            st.markdown('## Delete Current Experiment')
            st.markdown('**Warning**: This operation will delete current experiment record and result, which is irreversible.')
            if st.checkbox('Delete Current Experiment'):
                if st.button('Confirm'):
                    delete_current_experiment(db)

            cols_bottom = st.columns(2)
            
            with cols_bottom[0]:
                if st.button('Previous', disabled=st.session_state.cur_detail_id == min_id):
                    detect_experiment_id(db, False)
            with cols_bottom[1]:
                if st.button('Next', disabled=st.session_state.cur_detail_id == max_id):
                    detect_experiment_id(db)    

def detect_experiment_id(db, next_flag=True):
    experiment_list = db['experiment_list']
    if st.session_state.cur_detail_id is None:
        basic_info = experiment_list.select(other='ORDER BY id DESC LIMIT 1')
        if len(basic_info) == 0:
            return None
        st.session_state.cur_detail_id = basic_info[0]['id']
    else:
        basic_info = experiment_list.select(where=f'WHERE id{">" if next_flag else "<"}{st.session_state.cur_detail_id}', other='ORDER BY id ASC LIMIT 1')
        st.session_state.cur_detail_id = basic_info[0]['id']
        
def detect_experiment_info(db):
    experiment_list = db['experiment_list']
    basic_info = experiment_list.select(where=f'WHERE id={st.session_state.cur_detail_id}')
    method = basic_info[0]['method']
    method_id = basic_info[0]['method_id']
    method_info = None
    data = basic_info[0]['data']
    data_id = basic_info[0]['data_id']
    data_info = None
    result_info = None
    task = basic_info[0]['task']
    if method_id != -1:
        method_table = db[f'method_{method}']
        method_info = method_table.select(where=f'WHERE id={method_id}')
    if data_id != -1:
        data_table = db[f'data_{data}']
        data_info = data_table.select(where=f'WHERE id={data_id}')
    if basic_info[0]["status"] == 'finished':
        result_table = db[f'result_{task}']
        result_info = result_table.select(where=f'WHERE id={st.session_state.cur_detail_id}')
    return basic_info, method_info, data_info, result_info

def delete_current_experiment(db):
    experiment_list = db['experiment_list']
    task = experiment_list.select(where=f'id={st.session_state.cur_detail_id}')[0]['task']
    experiment_list.delete(f'id={st.session_state.cur_detail_id}')
    result_table = db[f'result_{task}']
    result_table.delete(f'id={st.session_state.cur_detail_id}')
    db.conn.commit()
    st.session_state.cur_detail_id = None

def title():
    st.title(f'Experiment Details')
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(f'Database Loaded (In {st.session_state.db_path})')
    else:
        st.write('No database loaded, please load a database first.')
    