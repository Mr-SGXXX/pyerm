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

import streamlit as st
import os
import platform
import shutil
import math
import subprocess
from importlib.metadata import version

from pyerm.database.utils import delete_failed_experiments
from pyerm.database.dbbase import Database
from pyerm.database.tables import ResultTable
from pyerm.webUI import PYERM_HOME

REPO_URL = "https://github.com/Mr-SGXXX/pyerm"

def home():
    title()
    st.write("---")
    cols = st.columns(2)
    with cols[0]:
        load_db()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        with cols[1]:
            st.markdown('### Delete Useless Data in Database')
            st.write("You can delete useless data in the database to save space, including:")
            delete_useless_figures()
            if st.checkbox('Delete all failed and stuck records', value=False):
                st.write('**Warning: This operation will delete all failed records and their results, which cannot be undone.**')
                st.write("_**Notice**: Experiments that have been running for more than 24 hours will also be seen as stucked and deleted._")
                if st.button(f"Confirm", key="delete_failed"):
                    db = Database(st.session_state.db_path, output_info=False)
                    delete_failed_experiments(db)
                    st.session_state.cur_detail_id = None
                    st.rerun()
            st.write("---")
            st.markdown('### Export Experiment Data')
            st.write('You can export the experiment data by using the following options:')
            if st.checkbox('Download Excel & Result Images as ZIP', value=False):
                st.write('_This will export all the experiment data in the database as Excel files and images, and pack them into a ZIP file._')
                st.write('_The analysis results and figures are not included._')
                st.write('_**Notice**: Please be patient, this process may take a long time when the database is large._')
                download_zip()
            if st.checkbox('Download raw db file', value=False):
                st.write('_This will download the raw database file._')
                download_db()
    st.write("---")
    clean_cache()
    if st.sidebar.button('Refresh', key='refresh'):
        st.rerun()


def title():
    st.title('Python Experiment Record Manager WebUI')
    st.markdown(f"**Version**: {version('pyerm')}")
    st.markdown(f"**GitHub Repository**: [{REPO_URL}]({REPO_URL})")
    st.markdown(f"**PyPI**: [PyERM](https://pypi.org/project/pyerm/)")
    st.markdown(f"**License**: MIT")
    st.markdown(f"**Author**: Yuxuan Shao")
    st.markdown(f"**Description**:")
    st.markdown(f"PyERM is a Python package for managing and visualizing experiment records.")
    st.markdown(f"This is the web user interface of the PyERM.")
    st.markdown(f"**Disclaimer**: This is a demo version. Bugs may exist. Use at your own risk.")

def load_db():
    st.markdown('## Load Database')
    st.markdown("**Notice:** _PyERM is based on SQLite database_")
    db_path = st.selectbox("Select Recorded Database File", st.session_state.db_path_list, index=st.session_state.db_path_list.index(st.session_state.db_path) if st.session_state.db_path in st.session_state.db_path_list else 0)
    if db_path is None:
        db_path = st.session_state.db_path
    if st.checkbox('Use a new local database file', value=False):
        db_path = st.text_input("New Database Absolute Path", value=st.session_state.db_path)
        st.session_state.db_path_list.append(db_path)
    if st.checkbox('Upload Database File from Local', value=False):
        st.write('_This will upload a database file to the server and save it in the cache folder, which will be used in this Web UI._')
        st.write('_**Notice**: Please make sure the database file is in SQLite format._')
        db_path = upload_db()
    if st.button('Change Database Path'):
        st.session_state.db_path = db_path
        st.rerun()
    st.write(f"Current database path: **{st.session_state.db_path}**")
    if os.path.exists(db_path) and db_path.endswith('.db'):
        st.write(f"Database found succesfully.")
        st.write(f"Dataset size: **{format_size(os.path.getsize(db_path))}**")
    else:
        st.write(f"Database not found. Please input the correct path.")

def export_data():
    output_dir_path = f"{PYERM_HOME}/.tmp"
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)
    db_name = os.path.basename(st.session_state.db_path)
    db_name = os.path.splitext(db_name)[0]
    zip_path = os.path.join(output_dir_path, f"{db_name}.zip")
    result1 = subprocess.run(["export_zip", st.session_state.db_path, output_dir_path])
    if result1.returncode == 0:
        with open(zip_path, "rb") as file:
            zip_file = file.read()
        shutil.rmtree(output_dir_path)
    return zip_file

def download_zip():
    version = Database(st.session_state.db_path).get_db_version()
    if st.session_state.zip is None or version != st.session_state.last_version:
        st.session_state.zip = export_data()
        st.session_state.last_version = version
    st.download_button(
            label="Download Excel&Images as ZIP",
            data=st.session_state.zip,
            file_name=f"{os.path.basename(os.path.splitext(st.session_state.db_path)[0])}.zip",
            mime="application/zip"
        )
        

def download_db():
    with open(st.session_state.db_path, "rb") as file:
        db = file.read()
    st.download_button(
            label="Download raw db file",
            data=db,
            file_name=f"{os.path.basename(st.session_state.db_path)}",
            mime="application/sqlite3"
        )

def delete_useless_figures():
    if st.checkbox('Delete Useless Figures', value=False):
        st.write('**Notice:**_This will delete all the figures of those experiment without remark name in the database to save space._')
        if st.button('Confirm', key="delete_useless_figures"):
            db = Database(st.session_state.db_path, output_info=False)
            experiment_table = db['experiment_list']
            useless_figures_ids = experiment_table.select('id', 'task', where="remark is NULL")
            for id, task in useless_figures_ids:
                result_table = ResultTable(db, task)
                result_table.update(where=f"experiment_id={id}", **{f'image_{i}_name': None for i in range(result_table.max_image_index + 1)})
                result_table.update(where=f"experiment_id={id}", **{f'image_{i}': None for i in range(result_table.max_image_index + 1)})
            db.conn.execute("VACUUM")
            db.conn.commit()
            st.write('Useless figures deleted successfully.')
            st.rerun()
            
    
def upload_db():
    upload_db_file = st.file_uploader("Upload Database File", type=['db'])
    if upload_db_file is not None:
        name = upload_db_file.name
        cache_path = os.path.join(PYERM_HOME, name)
        with open(cache_path, "wb") as file:
            file.write(upload_db_file.read())
    else:
        cache_path = ""
    return cache_path

def clean_cache():
    st.write('## Cache Files')
    st.write('Cache is used to store temporary files, such as configure files.')
    st.write(f'Cache folder is located at: **{PYERM_HOME}**')
    st.write(f'Cache folder size: **{get_folder_size(PYERM_HOME)}**')
    if st.checkbox('Show Cache Files Tree', value=False):
        build_tree_string(PYERM_HOME)
    if st.checkbox('I want to clean cache', value=False):
        st.write('_**Notice**: This will delete the cache folder and all its contents, which cannot be undone._')
        if st.button('Confirm', key='clean_cache'):
            st.session_state.db_path_list = []
            shutil.rmtree(PYERM_HOME)
            st.write('Cache cleaned successfully.')
            st.rerun()

def build_tree_string(path, level=0):
    items = sorted(os.listdir(path))
    for item in items:
        item_path = os.path.join(path, item)
        st.markdown(f"<p style='text-indent: {20 * (level + 1)}px;'>{'📄' if os.path.isfile(item_path) else '📂'} {item}</p>", unsafe_allow_html=True) 
        if os.path.isdir(item_path):
            build_tree_string(item_path, level + 1)
            

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return format_size(total_size)

def format_size(size_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    if size_bytes == 0:
        return "0 B"
    index = min(len(units) - 1, int(math.log(size_bytes, 1024)))
    size = size_bytes / (1024 ** index)
    return f"{size:.2f} {units[index]}"