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

import streamlit as st
import os

REPO_URL = "https://github.com/Mr-SGXXX/pyerm"

def home():
    title()
    load_db()

def title():
    st.title('Python Experiment Record Manager WebUI')
    st.markdown(f"**Version**: 0.2.1")
    st.markdown(f"**Repository**: [{REPO_URL}]({REPO_URL})")
    st.markdown(f"**License**: MIT")
    st.markdown(f"**Author**: Yuxuan Shao")
    st.markdown(f"**Description**: This is the web user interface of the Python Experiment Record Manager.")
    st.markdown(f"**Disclaimer**: This is a demo version. The actual version is not available yet.")

def load_db():
    st.markdown('## Load Database')
    db_path = st.text_input("Database Path", value=st.session_state.db_path)
    if st.button('Change Database Path'):
        st.session_state.db_path = db_path
    st.write(f"Current database path: {st.session_state.db_path}")
    if os.path.exists(db_path) and db_path.endswith('.db'):
        st.write(f"Database loaded succesfully.")
    else:
        st.write(f"Database not found. Please input the correct path.")
    

