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
from pyerm.webUI.utils import detect_languages

REPO_URL = "https://github.com/Mr-SGXXX/pyerm"

def home():
    title()
    st.write("---")
    

    cols = st.columns(2)
    with cols[0]:
        load_db()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        with cols[1]:
            st.markdown(st.session_state.lm["home.delete_useless_data_title"])
            st.write(st.session_state.lm["home.delete_useless_data_notice"])
            delete_useless_figures()
            if st.checkbox(st.session_state.lm["home.delete_failed_records_checkbox"], value=False):
                st.write(st.session_state.lm["home.delete_failed_records_warning"])
                st.write(st.session_state.lm["home.delete_failed_records_notice"])
                if st.button(st.session_state.lm["home.delete_failed_records_confirm_button"], key="delete_failed"):
                    db = Database(st.session_state.db_path, output_info=False)
                    delete_failed_experiments(db)
                    st.session_state.cur_detail_id = None
                    st.rerun()
            st.write("---")
            st.markdown(st.session_state.lm["home.export_data_title"])
            st.write(st.session_state.lm["home.export_data_notice"])
            if st.checkbox(st.session_state.lm["home.export_zip_checkbox"], value=False):
                st.write(st.session_state.lm["home.export_zip_notice1"])
                st.write(st.session_state.lm["home.export_zip_notice2"])
                st.write(st.session_state.lm["home.export_zip_notice3"])
                download_zip()
            if st.checkbox(st.session_state.lm["home.export_db_checkbox"], value=False):
                st.write(st.session_state.lm["home.export_db_notice"])
                download_db()
    st.write("---")
    change_language()
    st.write("---")
    clean_cache()
    if st.sidebar.button(st.session_state.lm["app.refresh"], key='refresh'):
        st.rerun()


def title():
    st.title(st.session_state.lm["home.title.title"])
    st.markdown(st.session_state.lm["home.title.version"].format(version=version('pyerm')))
    st.markdown(st.session_state.lm["home.title.repo"].format(REPO_URL=REPO_URL))
    st.markdown(st.session_state.lm["home.title.pypi"])
    st.markdown(st.session_state.lm["home.title.license"])
    st.markdown(st.session_state.lm["home.title.author"])
    st.markdown(st.session_state.lm["home.title.description"])
    st.markdown(st.session_state.lm["home.title.description1"])
    st.markdown(st.session_state.lm["home.title.description2"])
    st.markdown(st.session_state.lm["home.title.disclaimer"])

def change_language():
    st.markdown(st.session_state.lm["home.change_language.title"])
    st.write(st.session_state.lm["home.change_language.title_notice"])
    languages = detect_languages()
    language = st.selectbox(st.session_state.lm["home.change_language.language_select"], languages, index=languages.index(st.session_state.lm.language) if st.session_state.lm.language in languages else 0)
    if st.button(st.session_state.lm["home.change_language.change_language_button"]):
        st.session_state.lm.set_language(language)
        st.rerun()

def load_db():
    st.markdown(st.session_state.lm["home.load_db.title"])
    st.markdown(st.session_state.lm["home.load_db.title_notice"])
    db_path = st.selectbox(st.session_state.lm["home.load_db.database_select"], st.session_state.db_path_list, index=st.session_state.db_path_list.index(st.session_state.db_path) if st.session_state.db_path in st.session_state.db_path_list else 0)
    if db_path is None:
        db_path = st.session_state.db_path
    if st.checkbox(st.session_state.lm["home.load_db.new_remote_database_checkbox"], value=False):
        db_path = st.text_input(st.session_state.lm["home.load_db.new_remote_database_input"], value=st.session_state.db_path)
        st.session_state.db_path_list.append(db_path)
    if st.checkbox(st.session_state.lm["home.load_db.upload_database_checkbox"], value=False):
        st.write(st.session_state.lm["home.load_db.upload_database_notice1"])
        st.write(st.session_state.lm["home.load_db.upload_database_notice2"])
        db_path = upload_db()
    if st.button(st.session_state.lm["home.load_db.change_database_button"]):
        st.session_state.db_path = db_path
        st.rerun()
    st.write(st.session_state.lm["home.load_db.current_path_text"].format(DB_PATH=st.session_state.db_path))
    if os.path.exists(db_path) and db_path.endswith('.db'):
        st.write(st.session_state.lm["home.load_db.load_success_text1"])
        st.write(st.session_state.lm["home.load_db.load_success_text2"].format(FORMAT_SIZE=format_size(os.path.getsize(db_path))))
    else:
        st.write(st.session_state.lm["home.load_db.load_failed_text"])

def export_data():
    output_dir_path = f"{PYERM_HOME}/.tmp"
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)
    db_name = os.path.basename(st.session_state.db_path)
    db_name = os.path.splitext(db_name)[0]
    zip_path = os.path.join(output_dir_path, f"{db_name}.zip")
    result1 = subprocess.run(["pyerm_export_zip", st.session_state.db_path, output_dir_path])
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
            label=st.session_state.lm["home.download_zip_button"],
            data=st.session_state.zip,
            file_name=f"{os.path.basename(os.path.splitext(st.session_state.db_path)[0])}.zip",
            mime="application/zip"
        )
        

def download_db():
    with open(st.session_state.db_path, "rb") as file:
        db = file.read()
    st.download_button(
            label=st.session_state.lm["home.download_db_button"],
            data=db,
            file_name=f"{os.path.basename(st.session_state.db_path)}",
            mime="application/sqlite3"
        )

def delete_useless_figures():
    if st.checkbox(st.session_state.lm["home.delete_useless_figures.delete_figures_button"], value=False):
        st.write(st.session_state.lm["home.delete_useless_figures.delete_figures_notice"])
        if st.button(st.session_state.lm["home.delete_useless_figures.delete_figures_confirm_button"], key="delete_useless_figures"):
            db = Database(st.session_state.db_path, output_info=False)
            experiment_table = db['experiment_list']
            useless_figures_ids = experiment_table.select('id', 'task', where="remark is NULL")
            for id, task in useless_figures_ids:
                result_table = ResultTable(db, task)
                result_table.update(where=f"experiment_id={id}", **{f'image_{i}_name': None for i in range(result_table.max_image_index + 1)})
                result_table.update(where=f"experiment_id={id}", **{f'image_{i}': None for i in range(result_table.max_image_index + 1)})
            db.conn.execute("VACUUM")
            db.conn.commit()
            st.write(st.session_state.lm["home.delete_useless_figures.delete_figures_success_text"])
            st.rerun()
            
    
def upload_db():
    upload_db_file = st.file_uploader(st.session_state.lm["home.upload_db_text"], type=['db'])
    if upload_db_file is not None:
        name = upload_db_file.name
        cache_path = os.path.join(PYERM_HOME, name)
        with open(cache_path, "wb") as file:
            file.write(upload_db_file.read())
    else:
        cache_path = ""
    return cache_path

def clean_cache():
    st.write(st.session_state.lm["home.clean_cache.title"])
    st.write(st.session_state.lm["home.clean_cache.title_notice"])
    st.write(st.session_state.lm["home.clean_cache.cache_location_text"].format(PYERM_HOME=PYERM_HOME))
    st.write(st.session_state.lm["home.clean_cache.cache_size_text"].format(FOLDER_SIZE=get_folder_size(PYERM_HOME)))
    if st.checkbox(st.session_state.lm["home.clean_cache.cache_file_tree_checkbox"], value=False):
        build_tree_string(PYERM_HOME)
    if st.checkbox(st.session_state.lm["home.clean_cache.clean_cache_checkbox"], value=False):
        st.write(st.session_state.lm["home.clean_cache.clean_cache_notice1"])
        if st.button(st.session_state.lm["home.clean_cache.clean_cache_confirm_button"], key='clean_cache'):
            st.session_state.db_path_list = []
            shutil.rmtree(PYERM_HOME)
            st.write(st.session_state.lm["home.clean_cache.clean_cache_success_text"])
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