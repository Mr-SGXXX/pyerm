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

import pandas as pd
from PIL import Image
import base64
from io import BytesIO
import streamlit as st
import os
import re
from time import strftime, gmtime

from pyerm.database.dbbase import Database
from pyerm.webUI import PYERM_HOME

def tables():
    title()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        detect_tables()
        st.sidebar.write('## SQL Query')
        No_SQL_flag = False
        if st.sidebar.checkbox('Use Full SQL Sentense For Whole DB', False):
            input_full_sql()
        else:
            No_SQL_flag = True
        if st.sidebar.checkbox('Use SQL By Columns & Conditions & Tables', False):
            input_sql()
        else:
            if No_SQL_flag:
                st.session_state.sql = None
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
            if "SELECT" not in st.session_state.sql.upper():
                db.conn.execute(st.session_state.sql)
                st.session_state.sql = None
                st.rerun()
            else:
                df = pd.read_sql_query(st.session_state.sql, db.conn)
                st.write(f'### Used SQL: ({st.session_state.sql})')
        except Exception as e:
            st.write(f'### Used SQL: ({st.session_state.sql})')
            st.write('### SQL Error:')
            st.code(e)
            st.session_state.sql = None
            return
    else:
        data = db[table_name].select()
        columns = [column[0] if column[0] != "end_time" else "finish_time" for column in db.cursor.description]
        df = pd.DataFrame(data, columns=columns)
    
    
    columns_keep = [col for col in df.columns if not col.startswith("image_")]
    
    if 'failed_reason' in df.columns and len(df) > 0:
        df['failed_reason'] = df.apply(lambda x: fold_detail_row(x, 'failed_reason'), axis=1)
    if "useful_time_cost" in df.columns:
        df['useful_time_cost'] = df['useful_time_cost'].apply(lambda x: strftime('%H:%M:%S', gmtime(x)) if not pd.isnull(x) else x) 
    if "total_time_cost" in df.columns:
        df['total_time_cost'] = df['total_time_cost'].apply(lambda x: strftime('%H:%M:%S', gmtime(x)) if not pd.isnull(x) else x)
    
    df = df[columns_keep]
    download_table_as_csv(df)
    show_table(df, columns_keep)
    
    
def show_table(df, columns_keep):
    # divide the table into multi parts
    total_counts = len(df)
    st.sidebar.write('## Table Part Selection')
    if total_counts <= st.session_state.single_table_part_max_records:
        if 'failed_reason' in df.columns:
            st.write(df.to_html(escape=False, columns=columns_keep), unsafe_allow_html=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        cur_table_part = st.sidebar.number_input('Current Part:', value=1, min_value=1, max_value=(total_counts-1) // st.session_state.single_table_part_max_records + 1)
        cur_table_part -= 1
        df = df.iloc[cur_table_part * st.session_state.single_table_part_max_records: (cur_table_part + 1) * st.session_state.single_table_part_max_records]
        if 'failed_reason' in df.columns:
            st.write(df.to_html(escape=False, columns=columns_keep), unsafe_allow_html=True)
        else:
            st.dataframe(df, use_container_width=True, height=500)
    if st.sidebar.checkbox('Set Max Record Counts Per Part', False):
        single_table_part_max_records = st.sidebar.number_input('Max Records Per Part:', value=st.session_state.single_table_part_max_records, min_value=1, step=10)
        if st.sidebar.button('Confirm', key='confirm_single_table_part_max_records'):
            st.session_state.single_table_part_max_records = single_table_part_max_records
            st.rerun()
    st.sidebar.write(f'_{len(df)}/{total_counts} records in current page._')

def input_sql():
    st.sidebar.write('You can set the columns and condition for construct a select SQL sentense for the current table here.')
    condition = st.sidebar.text_input("Condition", value='', help='The condition for the select SQL sentense.')
    columns = st.sidebar.text_input("Columns", value='*', help='The columns for the select SQL sentense.')
    st.session_state.table_name = st.sidebar.text_input("Table", value=st.session_state.table_name, help='The table, view or query for the select SQL sentense.')
    if st.sidebar.button('Run', key="run_table_sql"):
        st.session_state.sql = f"SELECT {columns} FROM {st.session_state.table_name} WHERE {condition}" if condition else f"SELECT {columns} FROM {st.session_state.table_name}"
        st.session_state.sql.replace('"', "'")
        st.session_state.table_name = 'SQL Query Results'

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



