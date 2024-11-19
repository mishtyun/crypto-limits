import sqlite3

class SQLiteRepository:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts
            (user_id INTEGER, coin TEXT, target_price REAL, alert_type TEXT)
        ''')
        self.conn.commit()

    def add_alert(self, user_id, coin, target_price, alert_type):
        self.cursor.execute('''
        INSERT INTO alerts (user_id, coin, target_price, alert_type)
        VALUES (?, ?, ?, ?)
        ''', (user_id, coin, target_price, alert_type))
        self.conn.commit()

    def get_all_alerts(self):
        self.cursor.execute('SELECT * FROM alerts')
        return self.cursor.fetchall()

    def remove_alert(self, user_id, coin):
        self.cursor.execute('''
        DELETE FROM alerts
        WHERE user_id = ? AND coin = ?
        ''', (user_id, coin))
        self.conn.commit()

    def get_user_alerts(self, user_id):
        self.cursor.execute('SELECT coin, target_price, alert_type FROM alerts WHERE user_id = ?', (user_id,))
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()