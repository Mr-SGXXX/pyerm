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
from PIL import Image
import base64
from io import BytesIO
import streamlit as st
import os
import re
from time import strftime, gmtime

from pyerm.database.utils import delete_failed_experiments
from pyerm.database.dbbase import Database
from pyerm.webUI import PYERM_HOME

def tables():
    title()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        detect_tables()
        st.sidebar.write('## SQL Query')
        if st.sidebar.checkbox('Use Full SQL Sentense For Whole DB', False):
            input_full_sql()
        if st.sidebar.checkbox('Use SQL By Columns & Conditions & Tables', False):
            input_sql()
        select_tables()
    if st.sidebar.button('Refresh', key='refresh'):
        st.rerun()

def detect_tables():
    st.sidebar.markdown('## Detected Tables')
    db = Database(st.session_state.db_path, output_info=False)
    if len(db.table_names) == 0:
        st.write('No tables detected in the database.')
        return
    table_name = st.sidebar.radio('**Table to select**:', db.table_names + db.view_names)
    st.session_state.table_name = table_name

def select_tables():
    def fold_detail_row(row, col_name):
        if row[col_name]:
            detail = row[col_name].replace("\n", "<br>")
            return f'<details><summary>Details</summary>{detail}</details>'
        else:
            return 'None'

    db = Database(st.session_state.db_path, output_info=False)
    table_name:str = st.session_state.table_name
    st.write('## Table:', table_name)
    if st.session_state.sql is not None:
        try:
            df = pd.read_sql_query(st.session_state.sql, db.conn)
            st.write(f'### Used SQL: ({st.session_state.sql})')
            st.session_state.sql = None
        except Exception as e:
            st.write('SQL Error:', e)
            st.session_state.sql = None
            return
    else:
        data = db[table_name].select()
        columns = [column[0] if column[0] != "end_time" else "finish_time" for column in db.cursor.description]
        df = pd.DataFrame(data, columns=columns)
    
    
    columns_keep = [col for col in df.columns if not col.startswith("image_")]
    
    if table_name == 'experiment_list':
        if st.checkbox('Delete all failed and stuck records', value=False):
            st.write('**Warning: This operation will delete all failed records and their results, which cannot be undone.**')
            if st.button(f"Confirm"):
                delete_failed_experiments(db)
                st.rerun()
    if "failed_reason" in df.columns:
        df['failed_reason'] = df.apply(lambda x: fold_detail_row(x, 'failed_reason'), axis=1)
    if "useful_time_cost" in df.columns:
        df['useful_time_cost'] = df['useful_time_cost'].apply(lambda x: strftime('%H:%M:%S', gmtime(x)) if not pd.isnull(x) else x) 
    if "total_time_cost" in df.columns:
        df['total_time_cost'] = df['total_time_cost'].apply(lambda x: strftime('%H:%M:%S', gmtime(x)) if not pd.isnull(x) else x)
    
    df = df[columns_keep]
    download_table_as_csv(df)
    if table_name == 'experiment_list':
        st.write(df.to_html(escape=False, columns=columns_keep), unsafe_allow_html=True)
    else:
        st.write(df)

def input_sql():
    st.sidebar.write('You can set the columns and condition for construct a select SQL sentense for the current table here.')
    condition = st.sidebar.text_input("Condition", value='', help='The condition for the select SQL sentense.')
    columns = st.sidebar.text_input("Columns", value='*', help='The columns for the select SQL sentense.')
    st.session_state.table_name = st.sidebar.text_input("Table", value=st.session_state.table_name, help='The table, view or query for the select SQL sentense.')
    if st.sidebar.button('Run', key="run_table_sql"):
        st.session_state.sql = f"SELECT {columns} FROM {st.session_state.table_name} WHERE {condition}" if condition else f"SELECT {columns} FROM {st.session_state.table_name}"

def input_full_sql():
    st.sidebar.write('You can input a full SQL sentense here to select what you need and link different tables or views.')
    st.sidebar.write('_**Notice**: Drop, Delete are allowed here, but please be careful when using them._')
    sql = st.sidebar.text_area('SQL', value=None, height=200)
    if st.sidebar.button('Run', key='run_full_sql'):
        st.session_state.sql = sql
        st.session_state.table_name = 'SQL Query Results'

def download_table_as_csv(df):
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"{st.session_state.table_name}.csv",
        mime="text/csv"
    )

def title():
    st.title('Tables of the experiment records')
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(f'Database Loaded (In {st.session_state.db_path})')
    else:
        st.write('No database loaded, please load a database first.')



