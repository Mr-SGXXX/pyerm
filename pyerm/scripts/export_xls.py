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

import PIL.Image as Image
import io
import pandas as pd
import sqlite3
import argparse
import os

USER_HOME = os.path.expanduser('~')

def export_xls(db_path:str, output_path:str):
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    conn = sqlite3.connect(db_path)
    table_names = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')", conn)
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')

    for table_name in table_names['name']:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        columns_nonimg = [col for col in df.columns if not col.startswith("image_")]
        df[columns_nonimg].to_excel(writer, sheet_name=table_name, index=False)
    writer.close()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Export the content of a SQLite database to an Excel file")
    parser.add_argument('db_path', type=str, nargs='?', default=None, help='The path of the database file')
    parser.add_argument('output_path', type=str, nargs='?', default="./experiment_record.xls", help='The path of the output excel file')
    args = parser.parse_args()
    if args.db_path is None:
        args.db_path = os.path.join(USER_HOME, 'experiment.db')
    if not os.path.exists(args.db_path):
        print(f"Error: The database file {args.db_path} does not exist, please run any experiment first or check the database path.")
        return
    export_xls(args.db_path, args.output_path)

if __name__ == "__main__":
    main()
