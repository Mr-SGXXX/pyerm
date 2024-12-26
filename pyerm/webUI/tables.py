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
        st.sidebar.write(st.session_state.lm["table.sidebar_sql_title"])
        No_SQL_flag = False
        if st.sidebar.checkbox(st.session_state.lm["table.sidebar_full_sql_checkbox"], False):
            input_full_sql()
        else:
            No_SQL_flag = True
        if st.sidebar.checkbox(st.session_state.lm["table.sidebar_sql_checkbox"], False):
            input_sql()
        else:
            if No_SQL_flag:
                st.session_state.sql = None
        select_tables()
    if st.sidebar.button(st.session_state.lm["app.refresh"], key='refresh'):
        st.rerun()

def detect_tables():
    st.sidebar.markdown(st.session_state.lm["table.detect_tables.title"])
    db = Database(st.session_state.db_path, output_info=False)
    if len(db.table_names) == 0:
        st.write(st.session_state.lm["table.detect_tables.no_table_detected_text"])
        return
    table_name = st.sidebar.radio(st.session_state.lm["table.detect_tables.table_select"], db.table_names + db.view_names)
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
    st.write(st.session_state.lm["table.select_tables.title"], table_name)
    if st.session_state.sql is not None:
        try:
            if "SELECT" not in st.session_state.sql.upper():
                db.conn.execute(st.session_state.sql)
                st.session_state.sql = None
                st.rerun()
            else:
                df = pd.read_sql_query(st.session_state.sql, db.conn)
                st.write(st.session_state.lm["table.select_tables."].format(SQL=st.session_state.sql))
        except Exception as e:
            st.write(st.session_state.lm["table.select_tables."].format(SQL=st.session_state.sql))
            st.write(st.session_state.lm["table.select_tables.sql_error"])
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
    st.sidebar.write(st.session_state.lm["table.show_table.sidebar_title"])
    if total_counts <= st.session_state.single_table_part_max_records:
        if 'failed_reason' in df.columns:
            st.write(df.to_html(escape=False, columns=columns_keep), unsafe_allow_html=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        cur_table_part = st.sidebar.number_input(st.session_state.lm["table.show_table.sidebar_part_input"], value=1, min_value=1, max_value=(total_counts-1) // st.session_state.single_table_part_max_records + 1)
        cur_table_part -= 1
        df = df.iloc[cur_table_part * st.session_state.single_table_part_max_records: (cur_table_part + 1) * st.session_state.single_table_part_max_records]
        if 'failed_reason' in df.columns:
            st.write(df.to_html(escape=False, columns=columns_keep), unsafe_allow_html=True)
        else:
            st.dataframe(df, use_container_width=True, height=500)
    if st.sidebar.checkbox(st.session_state.lm["table.show_table.sidebar_set_max_checkbox"], False):
        single_table_part_max_records = st.sidebar.number_input(st.session_state.lm["table.show_table.sidebar_set_max_input"], value=st.session_state.single_table_part_max_records, min_value=1, step=10)
        if st.sidebar.button(st.session_state.lm["table.show_table.sidebar_set_max_confirm_button"], key='confirm_single_table_part_max_records'):
            st.session_state.single_table_part_max_records = single_table_part_max_records
            st.rerun()
    st.sidebar.write(st.session_state.lm["table.show_table.sidebar_show_cur_counts"].format(CUR_COUNTS=len(df), TOTAL_COUNTS=total_counts))

def input_sql():
    st.sidebar.write(st.session_state.lm["table.input_sql.text"])
    condition = st.sidebar.text_input(st.session_state.lm["table.input_sql.condition_input"], value='', 
                                      help=st.session_state.lm["table.input_sql.condition_help"])
    columns = st.sidebar.text_input(st.session_state.lm["table.input_sql.columns_input"], value='*', 
                                    help=st.session_state.lm["table.input_sql.columns_help"])
    st.session_state.table_name = st.sidebar.text_input(st.session_state.lm["table.input_sql.table"], value=st.session_state.table_name, help='The table, view or query for the select SQL sentense.')
    if st.sidebar.button(st.session_state.lm["table.input_sql.run_button"], key="run_table_sql"):
        st.session_state.sql = f"SELECT {columns} FROM {st.session_state.table_name} WHERE {condition}" if condition else f"SELECT {columns} FROM {st.session_state.table_name}"
        st.session_state.sql.replace('"', "'")
        st.session_state.table_name = st.session_state.lm["table.input_sql.table_name"]

def input_full_sql():
    st.sidebar.write(st.session_state.lm["table.input_full_sql.text"])
    st.sidebar.write(st.session_state.lm["table.input_full_sql.notice"])
    sql = st.sidebar.text_area('SQL', value=None, height=200)
    if st.sidebar.button(st.session_state.lm["table.input_full_sql.run_button"], key='run_full_sql'):
        st.session_state.sql = sql
        st.session_state.table_name = st.session_state.lm["table.input_full_sql.table_name"]

def download_table_as_csv(df):
    csv = df.to_csv(index=False)
    st.download_button(
        label=st.session_state.lm["table.download_table_as_csv_button"],
        data=csv,
        file_name=f"{st.session_state.table_name}.csv",
        mime="text/csv"
    )

def title():
    st.title(st.session_state.lm["table.title"])
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(st.session_state.lm["app.dataset_load_success_text"].format(DB_PATH=st.session_state.db_path))
    else:
        st.write(st.session_state.lm["app.dataset_load_failed_text"])