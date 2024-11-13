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

# Version: 0.2.9

import pandas as pd
import streamlit as st
import os
from PIL import Image
import re
import io

from pyerm.database.dbbase import Database
from pyerm.database.utils import get_result_statistics
from pyerm.webUI import PYERM_HOME

def analysis():
    title()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        db = Database(st.session_state.db_path, output_info=False)
        analysis_task = sidebar_select_analysis()
        if analysis_task == 'Single Setting Analysis':
            task, method, method_id, dataset, dataset_id = select_setting(db)
            st.write('---')
            st.write('### Statistics Results')
            result_statistics, num_records = get_result_statistics(db, task, method, method_id, dataset, dataset_id)
            if result_statistics is not None:
                st.dataframe(result_statistics)
                st.write(f"_**Notice**: The statistics are calculated based on the **{num_records}** same setting experiments._")
            else:
                st.write('No statistics results found for this setting.')
        elif analysis_task == 'Multi Setting Analysis':
            
            task, method, method_id, dataset, dataset_id = select_setting(db)
            if st.button('Record Current Setting', key='add_setting'):
                st.session_state.recorded_analysis_setting.add((task, method, method_id, dataset, dataset_id))
                st.rerun()
            st.write('---')
            st.sidebar.write('### Selected Settings')
            selected_settings = []
            for setting in st.session_state.recorded_analysis_setting:
                if st.sidebar.checkbox(f'{setting[0]}-{setting[1]}-{setting[3]}-{setting[4]}'):
                    selected_settings.append(setting)
            st.sidebar.write(selected_settings)
    if st.sidebar.button('Refresh', key='refresh'):
        st.rerun()
            
            

def sidebar_select_analysis():
    st.sidebar.markdown('## Experiment Analysis')
    return st.sidebar.radio('**Analysis Task**:', ['Single Setting Analysis', 'Different Setting Analysis', ])
        
    
def select_setting(db):
    st.write('### Select Experiment Settings')
    cols = st.columns(3)
    with cols[0]:
        st.write('**Select Task**')
        task_sql = f'SELECT DISTINCT task FROM experiment_list'
        tasks = [t[0] for t in db.conn.execute(task_sql).fetchall()]
        task = st.selectbox('Task:', tasks)
        
    with cols[1]:
        st.write('**Select Method**')
        method_sql = f'SELECT DISTINCT method FROM experiment_list WHERE task="{task}"'
        methods = [m[0] for m in db.cursor.execute(method_sql).fetchall()]
        method = st.selectbox('Method:', methods)
        method_id_sql = f'SELECT DISTINCT method_id FROM experiment_list WHERE task = "{task}" AND method = "{method}"'
        method_ids = [m[0] for m in db.conn.execute(method_id_sql).fetchall()]
        method_id = st.selectbox('Method Setting ID:', method_ids)
        if method_id != -1:
            method_table = db[f'method_{method}']
            method_info = method_table.select(where=f'method_id={method_id}')
            method_columns = method_table.columns
            method_info = pd.DataFrame(method_info, columns=method_columns)
            method_info.index = [f'Current Setting']
            st.dataframe(method_info.astype(str).transpose(), use_container_width=True, height=150)
        else:
            st.write('No Parameters for this method')
        
        
    with cols[2]:
        st.write("**Select Data**")
        dataset_sql = f'SELECT DISTINCT data FROM experiment_list WHERE task = "{task}" AND method = "{method}" AND method_id = "{method_id}"'
        datasets = [d[0] for d in db.conn.execute(dataset_sql).fetchall()]
        dataset = st.selectbox('Dataset:', datasets)
        dataset_id_sql = f'SELECT DISTINCT data_id FROM experiment_list WHERE task = "{task}" AND method = "{method}" AND method_id = "{method_id}" AND data = "{dataset}"'
        dataset_ids = [d[0] for d in db.conn.execute(dataset_id_sql).fetchall()]
        dataset_id = st.selectbox('Dataset Setting ID:', dataset_ids)
        if dataset_id != -1:
            data_table = db[f'data_{dataset}']
            data_info = data_table.select(where=f'data_id={dataset_id}')
            data_columns = data_table.columns
            data_info = pd.DataFrame(data_info, columns=data_columns)
            data_info.index = [f'Current Setting']
            st.dataframe(data_info.astype(str).transpose(), use_container_width=True, height=150)
        else:
            st.write('No Parameters for this dataset')
        
    return task, method, method_id, dataset, dataset_id
        

def title():
    st.title(f'Experiment Analysis')
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(f'Database Loaded (In {st.session_state.db_path})')
    else:
        st.write('No database loaded, please load a database first.')