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

# Version: 0.1.9
import sqlite3
import argparse
import os

from pyerm.database.dbbase import Table, Database

def copy_table(db1:Database, db2:Database, table_name:str):
    table = Table(db2, table_name)
    columns = [info[1] for info in db2.cursor.execute(f"PRAGMA table_info({table_name})").fetchall() if info[1] not in table.primary_key]
    columns_list_str = ', '.join(columns)  
    placeholders = ', '.join(['?'] * len(columns))  
    insert_stmt = f"INSERT INTO {table_name} ({columns_list_str}) VALUES ({placeholders})"
    rows = db2.cursor.execute(f"SELECT {columns_list_str} FROM {table_name}").fetchall()
    for row in rows:
        try:
            db1.cursor.execute(insert_stmt, row)
        except sqlite3.IntegrityError:
            pass
    db1.conn.commit()

def merge_db(db_path1:str, db_path2:str):
    db1 = Database(db_path1)
    db2 = Database(db_path2)
    for table_name in db2.table_names:
        copy_table(db1, db2, table_name)

def main():
    parser = argparse.ArgumentParser(description='Merge two SQLite databases. For now, the merged two databases must have the same schema.')
    parser.add_argument('db_path_destination', type=str, help='Destination database file path.')
    parser.add_argument('db_path_source', type=str, help='Source database file path.')
    args = parser.parse_args()
    if not os.path.exists(args.db_path_destination):
        raise FileNotFoundError(f"The database file {args.db_path_destination} does not exist")
    if not os.path.exists(args.db_path_source):
        raise FileNotFoundError(f"The database file {args.db_path_source} does not exist")
    merge_db(args.db_path_destination, args.db_path_source)


if __name__ == "__main__":
    main()