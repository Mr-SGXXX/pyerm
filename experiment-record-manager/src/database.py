import sqlite3

class Database:
    def __init__(self, db_path:str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.table_names = [table_name[0] for table_name in self.cursor.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()]

    def create_table(self, table_name:str, columns:dict) -> None:
        columns_str = ', '.join([f'{key} {value}' for key, value in columns.items()])
        self.cursor.execute(f'CREATE TABLE IF NOT EXIST {table_name} ({columns_str})')
        self.conn.commit()
    
    def __getitem__(self, table_name:str):
        if table_name not in self.table_names:
            raise ValueError(f'Table {table_name} does not exist')
        return Table(self, table_name)

class Table:
    def __init__(self, db:Database, table_name:str) -> None:
        self.db = db
        self.table_name = table_name
        self.columns = [column[1] for column in self.db.cursor.execute(f'PRAGMA table_info({table_name})').fetchall()]
        self.primary_key = [column[5] for column in self.db.cursor.execute(f'PRAGMA table_info({table_name})').fetchall() if column[5] == 1]
    
    def insert(self, **kwargs) -> None:
        columns = ', '.join(kwargs.keys())
        values = ', '.join([f'"{value}"' if isinstance(value, str) else str(value) for value in kwargs.values()])
        self.db.cursor.execute(f'INSERT INTO {self.table_name} ({columns}) VALUES ({values})')
        self.db.conn.commit()

    def delete(self, where:str) -> None:
        self.db.cursor.execute(f'DELETE FROM {self.table_name} WHERE {where}')
        self.db.conn.commit()
    
    def update(self, where:str, **kwargs) -> None:
        set_values = ', '.join([f'{key}="{value}"' if isinstance(value, str) else f'{key}={value}' for key, value in kwargs.items()])
        self.db.cursor.execute(f'UPDATE {self.table_name} SET {set_values} WHERE {where}')
        self.db.conn.commit()
    
    def select(self, *columns:str, where:str=None) -> list:
        columns = ', '.join(columns) if columns else '*'
        where = f'WHERE {where}' if where else ''
        return self.db.cursor.execute(f'SELECT {columns} FROM {self.table_name} {where}').fetchall()