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

# Version: 0.2.2

import streamlit as st
import os

from home import home
from tables import tables

USER_HOME = os.path.expanduser('~')

def init():
    if 'db_path' not in st.session_state:
        st.session_state.db_path = os.path.join(USER_HOME, 'experiment.db')
    if 'table_name' not in st.session_state:
        st.session_state.table_name = None
    if 'sql' not in st.session_state:
        st.session_state.sql = None
    if 'xls' not in st.session_state:
        st.session_state.xls = None


def main():
    init()
    st.set_page_config(page_title="PyERM WebUI", page_icon="📊", layout="wide", initial_sidebar_state="auto")
    st.sidebar.title("PyERM WebUI")
    st.sidebar.markdown("## Please select a page")
    page = st.sidebar.radio("Page to select:", ["Home", "Tables"], index=0)
    if page == "Home":
        home()
    elif page == "Tables":
        tables()


if __name__ == "__main__":
    main()
