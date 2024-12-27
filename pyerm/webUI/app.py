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
import configparser

from home import home
from record import record
from tables import tables
from details import details
from analysis import analysis
import warnings

from pyerm.webUI import PYERM_HOME
from pyerm.webUI.utils import LanguageManager


def init():
    warnings.filterwarnings("ignore", category=UserWarning)
    config = configparser.ConfigParser()
    if not os.path.exists(PYERM_HOME):
        os.makedirs(PYERM_HOME)
        config.set('DEFAULT', 'db_path', os.path.join(PYERM_HOME, 'experiment.db'))
        config.set('DEFAULT', 'language', 'English')
    else:
        config.read(os.path.join(PYERM_HOME, 'config.ini'))
        
    if 'db_path' not in st.session_state:
        db_path_list = config.get('DEFAULT', 'db_path', fallback=os.path.join(PYERM_HOME, 'experiment.db'))
        st.session_state.db_path_list = db_path_list.split(',')
        st.session_state.db_path = st.session_state.db_path_list[0]
    else:
        db_path_list = config.get('DEFAULT', 'db_path', fallback=os.path.join(PYERM_HOME, 'experiment.db'))
        db_path_list = db_path_list.split(',')
        db_path_list = [db_path for db_path in db_path_list if os.path.exists(db_path)]
        if st.session_state.db_path not in db_path_list and os.path.exists(st.session_state.db_path):
            db_path_list.append(st.session_state.db_path)
        st.session_state.db_path_list = db_path_list
        config.set('DEFAULT', 'db_path', ','.join(db_path_list))
    if 'lm' not in st.session_state:
        st.session_state.lm = LanguageManager(config.get('DEFAULT', 'language', fallback='English'))
    else:
        config.set('DEFAULT', 'language', st.session_state.lm.language)
    if 'table_name' not in st.session_state:
        st.session_state.table_name = None
    if 'sql' not in st.session_state:
        st.session_state.sql = None
    if 'zip' not in st.session_state:
        st.session_state.zip = None
    if 'last_version' not in st.session_state:
        st.session_state.last_version = None
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None
    if 'cur_detail_id' not in st.session_state:
        st.session_state.cur_detail_id = None
    if 'cur_detail_img_id' not in st.session_state:
        st.session_state.cur_detail_img_id = None
    if 'recorded_analysis_setting' not in st.session_state:
        st.session_state.recorded_analysis_setting = []
    if 'selected_settings' not in st.session_state:
        st.session_state.selected_settings = []
    if 'error_flag' not in st.session_state:
        st.session_state.error_flag = False
    if 'error_flag1' not in st.session_state:
        st.session_state.error_flag1 = False
    if 'cur_analysis_task' not in st.session_state:
        st.session_state.cur_analysis_task = None
    if 'single_table_part_max_records' not in st.session_state:
        st.session_state.single_table_part_max_records = int(config.get('DEFAULT', 'single_table_part_max_records', fallback=100))
    else:
        config.set('DEFAULT', 'single_table_part_max_records', str(st.session_state.single_table_part_max_records))
    with open(os.path.join(PYERM_HOME, 'config.ini'), 'w') as f:
        config.write(f)

def main():
    init()
    st.set_page_config(page_title="PyERM WebUI", page_icon="📊", layout="wide", initial_sidebar_state="auto")
    st.sidebar.title("PyERM WebUI")
    st.sidebar.markdown(st.session_state.lm["app.sidebar_page_select"])
    
    page = st.sidebar.radio(st.session_state.lm["app.sidebar_page_select_radio"],
            [
                st.session_state.lm["app.sidebar_page_select_radio_1"],
                st.session_state.lm["app.sidebar_page_select_radio_2"], 
                st.session_state.lm["app.sidebar_page_select_radio_3"], 
                st.session_state.lm["app.sidebar_page_select_radio_4"], 
                st.session_state.lm["app.sidebar_page_select_radio_5"]
            ], index=0)

    if page == st.session_state.lm["app.sidebar_page_select_radio_1"]:
        home()
    elif page == st.session_state.lm["app.sidebar_page_select_radio_2"]:
        record()
    elif page == st.session_state.lm["app.sidebar_page_select_radio_3"]:
        details()
    elif page == st.session_state.lm["app.sidebar_page_select_radio_4"]:
        analysis()
    elif page == st.session_state.lm["app.sidebar_page_select_radio_5"]:
        tables()
        
    

if __name__ == "__main__":
    main()
