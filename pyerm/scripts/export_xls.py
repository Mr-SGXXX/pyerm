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

# Version: 0.1.4

import pandas as pd
import sqlite3
import argparse
import os

USER_HOME = os.path.expanduser('~')

def export_xls(db_path:str, output_path:str):
    conn = sqlite3.connect(db_path)
    table_names = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')", conn)
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    for table_name in table_names['name']:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        df.to_excel(writer, sheet_name=table_name, index=False)
    conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path', type=str, default= os.path.join(USER_HOME, 'experiment.db'), help='The path of the database file')
    parser.add_argument('output_path', type=str, help='The path of the output excel file')
    args = parser.parse_args()
    export_xls(args.db_path, args.output_path)

if __name__ == "__main__":
    main()
