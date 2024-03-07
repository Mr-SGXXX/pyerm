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

import sqlite3
import re

class Database:
    def __init__(self, db_path:str, output_info=True) -> None:
        self.db_path = db_path
        self.info = output_info
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.table_names = [table_name[0] for table_name in self.cursor.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()]
        self.view_names = [view_name[0] for view_name in self.cursor.execute('SELECT name FROM sqlite_master WHERE type="view"').fetchall()]


    def __getitem__(self, name:str):
        if name in self.table_names:
            return Table(self, name)
        elif name in self.view_names:
            return View(self, name)
        else:
            raise ValueError(f'Table or View {name} does not exist')
        
    def __setitem__(self, name:str, columns:dict=None, query:str=None):
        if columns is not None and query is None:
            return Table(self, name, columns)
        elif columns is None and query is not None:
            return View(self, name, query)
        else:
            raise ValueError('Either columns or query must be provided and the other must be None')
    
    def __delitem__(self, name:str):
        if name in self.table_names:
            self.cursor.execute(f'DROP TABLE {name}')
            self.table_names.remove(name)
        elif name in self.view_names:
            self.cursor.execute(f'DROP VIEW {name}')
            self.view_names.remove(name)
        self.conn.commit()

    def __len__(self):
        return len(self.table_names)
    
    def __del__(self):
        self.cursor.close()
        self.conn.close()
    
    def get_table(self, table_name:str):
        return self[table_name]

class Table:
    def __init__(self, db:Database, table_name:str, columns:dict=None) -> None:
        self.db = db
        self.table_name = table_name
        self._column = None
        if not table_exists(db, table_name):
            assert columns, 'Columns must be provided when creating a new table'
            columns_str = ', '.join([f'{key} {value}' for key, value in columns.items()])
            self.db.cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})')
            self.db.conn.commit()
            self.db.table_names.append(table_name)
            if self.db.info:
                print(f'Table {table_name} created')
        else:
            if columns is not None:
                for column, definition in list(columns.items()):
                    if 'VIRTUAL' in definition:
                        del columns[column]
            assert columns is None or list(columns.keys()) == list([column[1] for column in self.db.cursor.execute(f'PRAGMA table_info({table_name})').fetchall()]), f'Columns do not match for table {table_name}, consider to check or change table name'
            if self.db.info:
                print(f'Table {table_name} already exists')
        self.primary_key = [column[1] for column in self.db.cursor.execute(f'PRAGMA table_info({table_name})').fetchall() if column[5] == 1]
    
    def insert(self, **kwargs) -> int:
        assert len(kwargs) <= len(self.columns), 'Parameter inputted too much'
        columns = ', '.join(kwargs.keys())
        values = ', '.join(['?' for _ in kwargs])
        query = f'INSERT INTO {self.table_name} ({columns}) VALUES ({values})'
        self.db.cursor.execute(query, tuple(kwargs.values()))
        self.db.conn.commit()
        return self.db.cursor.lastrowid

    def delete(self, where:str) -> None:
        query = f'DELETE FROM {self.table_name} WHERE {where}'
        self.db.cursor.execute(query)
        self.db.conn.commit()

    def update(self, where:str, **kwargs) -> None:
        set_values = ', '.join([f'{key}=?' for key in kwargs])
        query = f'UPDATE {self.table_name} SET {set_values} WHERE {where}'
        self.db.cursor.execute(query, tuple(kwargs.values()))
        self.db.conn.commit()

    def select(self, *columns:str, where:str=None) -> list:
        columns_str = ', '.join(columns) if columns else '*'
        where_clause = f'WHERE {where}' if where else ''
        query = f'SELECT {columns_str} FROM {self.table_name} {where_clause}'
        return self.db.cursor.execute(query).fetchall()

    @property
    def columns(self):
        if self._column is None:
            self._column = [column[1] for column in self.db.cursor.execute(f'PRAGMA table_info({self.table_name})').fetchall()]
        return self._column

    def __len__(self):
        return len(self.select())
    
    def __getitem__(self, index:int):
        return self.select()[index]
    
    def __iter__(self):
        return iter(self.select())
    
    def __str__(self) -> str:
        return str([column[1] for column in self.db.cursor.execute(f'PRAGMA table_info({self.table_name})').fetchall()]) + '\n' + \
                str([column[2] for column in self.db.cursor.execute(f'PRAGMA table_info({self.table_name})').fetchall()]) + '\n' + \
                str(self.select())

class View:
    def __init__(self, db:Database, view_name:str, query:str=None) -> None:
        self.db = db
        self.view_name = view_name
        if not view_exists(db, view_name):
            assert query, 'Query must be provided when creating a new view'
            self.db.cursor.execute(f'CREATE VIEW IF NOT EXISTS {view_name} AS {query}')
            self.query = query
            self.db.conn.commit()
            self.db.view_names.append(view_name)
            if self.db.info:
                print(f'View {view_name} created')
        else:
            self.db.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='view' AND name='{self.view_name}'")
            self.query = self.db.cursor.fetchone()[0]
            if self.db.info:
                print(f'View {view_name} already exists')
    
    def select(self, *columns:str, where:str=None) -> list:
        columns = ', '.join(columns) if columns else '*'
        where = f'WHERE {where}' if where else ''
        return self.db.cursor.execute(f'SELECT {columns} FROM {self.view_name} {where}').fetchall()
    
    @property
    def columns(self):
        columns = self.query.split('SELECT ')[1].split(' FROM')[0].split(',')
        column_names = [col.strip() for col in columns]

        return column_names

    def __getitem__(self, index:int):
        return self.select()[index]

    def __len__(self):
        return len(self.select())
    
    def __iter__(self):
        return iter(self.select())

    def __del__(self):
        self.db.cursor.execute(f'DROP VIEW {self.view_name}')
        self.db.conn.commit()

    def __str__(self) -> str:
        return str([column for column in self.columns]) + '\n' + \
                str(self.select())
    
def table_exists(db:Database, table_name:str):
    cursor = db.cursor

    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = cursor.fetchone()

    if result:
        return True
    else:
        return False
    
def view_exists(db:Database, view_name:str):
    cursor = db.cursor

    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view_name}'")
    result = cursor.fetchone()

    if result:
        return True
    else:
        return False

def extract_names(sql_statement):
    pattern = r'(?:FROM|JOIN|UPDATE|INSERT INTO)\s+(\w+)'
    table_names = re.findall(pattern, sql_statement, re.IGNORECASE)
    pattern = r'CREATE\s+(TABLE|VIEW)\s+(\w+)'
    created_tables = re.findall(pattern, sql_statement, re.IGNORECASE)
    return table_names + created_tables
