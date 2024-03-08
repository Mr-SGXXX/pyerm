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

# Version: 0.2.1

import pandas as pd
import streamlit as st
import os

from pyerm.dbbase import Database

def tables():
    title()
    st.sidebar.markdown('## Detected Tables')
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        detect_tables()
        if st.sidebar.checkbox('Use SQL condition & columns', False):
            input_sql()
        select_tables()
    else:
        st.write('No database loaded, please load a database first.')

def detect_tables():
    db = Database(st.session_state.db_path, output_info=False)
    if len(db.table_names) == 0:
        st.write('No tables detected in the database.')
        return
    table_name = st.sidebar.radio('Table to select:', db.table_names + db.view_names)
    st.session_state.table_name = table_name

def select_tables():
    db = Database(st.session_state.db_path, output_info=False)
    table_name = st.session_state.table_name
    if st.session_state.sql is not None:
        try:
            table_name = st.session_state.table_name
            df = pd.read_sql_query(st.session_state.sql, db.conn)
            st.session_state.sql = None
        except Exception as e:
            st.write('Error:', e)
            st.session_state.sql = None
            return
    else:
        data = db[table_name].select()
        columns = [column[0] for column in db.cursor.description]
        df = pd.DataFrame(data, columns=columns)
    columns_keep = [col for col in df.columns if not col.startswith("image_")]
    df = df[columns_keep]

    st.write('## Table:', table_name)
    st.dataframe(df)
    

def input_sql():
    st.sidebar.write('You can also set the columns and condition for construct a select SQL sentense for the current table here.')
    condition = st.sidebar.text_input("Condition", value='', help='The condition for the select SQL sentense.')
    columns = st.sidebar.text_input("Columns", value='*', help='The columns for the select SQL sentense.')
    if st.sidebar.button('Run'):
        st.session_state.sql = f"SELECT {columns} FROM {st.session_state.table_name} WHERE {condition}" if condition else f"SELECT {columns} FROM {st.session_state.table_name}"


def title():
    st.title('Tables of the experiments')
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(f'Database Loaded (In {st.session_state.db_path})')
    else:
        st.write('No database loaded, please load a database first.')



