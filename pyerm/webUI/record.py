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
import streamlit as st
import os
from PIL import Image
import re
import io
import matplotlib.pyplot as plt
import seaborn as sns
import typing

from pyerm.database.dbbase import Database
from pyerm.database.experiment import Experiment

def record():
    title()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(st.session_state.lm["record.manually_record_title"])
            
    if st.sidebar.button(st.session_state.lm["app.refresh"], key='refresh'):
        st.rerun()
        

def title():
    st.title(st.session_state.lm["record.title"])
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(st.session_state.lm["app.dataset_load_success_text"].format(DB_PATH=st.session_state.db_path))
    else:
        st.write(st.session_state.lm["app.dataset_load_failed_text"])