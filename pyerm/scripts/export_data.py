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

# Version: 0.2.4

import PIL.Image as Image
import io
import pandas as pd
import sqlite3
import argparse
import os
import shutil
from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor

USER_HOME = os.path.expanduser('~')

def save_image(row, col, output_img_dir, output_path):
    img_data = getattr(row, col)
    if img_data is not None:
        img = Image.open(io.BytesIO(img_data))
        img_abs_path = os.path.join(output_img_dir, f"ID{row.experiment_id}_{col}.png")
        img.save(img_abs_path)
        img_rel_path = os.path.relpath(img_abs_path, os.path.dirname(output_path))
        return img_rel_path
    return None

def export_data(db_path:str, output_dir:str):
    db_name = os.path.basename(db_path)
    db_name = os.path.splitext(db_name)[0]
    output_path = os.path.join(output_dir, db_name, f"{db_name}.xlsx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_img_dir = os.path.join(os.path.dirname(output_path), "result_imgs")
    os.makedirs(output_img_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    table_names = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')", conn)
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')

    for table_name in table_names['name']:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        if table_name.startswith("result_"):
            for col in df.columns:
                if col.startswith("image_") and not col.endswith("_name") and not df[f"{col}_name"].isnull().all():
                    with ThreadPoolExecutor() as executor:
                        img_paths = list(executor.map(lambda row: save_image(row, col, output_img_dir, output_path), df.itertuples()))
                    df[col] = img_paths
        df.to_excel(writer, sheet_name=table_name, index=False)
        if table_name.startswith("result_"):
            workbook  = writer.book
            worksheet = writer.sheets[table_name]
            for col_num, col in enumerate(df.columns):
                if col.startswith("image_") and not col.endswith("_name"):
                    for row_num, cell_value in enumerate(df[col], start=1):
                        if cell_value is not None:
                            worksheet.write_url(row_num, col_num, cell_value, string=df[f"{col}_name"][row_num-1])
    writer.close()
    conn.close()
    zip_path = os.path.join(output_dir, f"{db_name}.zip")
    zip_dir(os.path.dirname(output_path), zip_path, remove_original=True)
    return zip_path

def zip_dir(dir_path:str, zip_path:str, remove_original=False):
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, dir_path))
    if remove_original:
        shutil.rmtree(dir_path)
        


def main():
    parser = argparse.ArgumentParser(description="Export the content of a SQLite database to an Excel file")
    parser.add_argument('db_path', type=str, nargs='?', default=None, help='The path of the database file')
    parser.add_argument('output_dir', type=str, nargs='?', default="./", help='The dir path of the output file')
    args = parser.parse_args()
    if args.db_path is None:
        args.db_path = os.path.join(USER_HOME, 'experiment.db')
    if not os.path.exists(args.db_path):
        print(f"Error: The database file {args.db_path} does not exist, please run any experiment first or check the database path.")
        return
    export_data(args.db_path, args.output_dir)

if __name__ == "__main__":
    main()
