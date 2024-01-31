import sqlite3
from datetime import datetime

class sqlManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.create_table()


    def create_table(self):
        # Create the events table if it doesn't exist
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                title TEXT
            )
        ''')
        self.conn.commit()

    def store_alarms(self, events):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM events")
        self.conn.commit()

        for event in events:
            # for key, value in event.items():
            #     print(f"{key}: {value}, Type: {type(value)}")
            event_id = event['event_id']
            date = event['date']
            start_time = event['start_time']
            end_time = event['end_time']
            title = event['title']
            # Convert the date to a string in the 'YYYY-MM-DD' format
            cursor.execute("INSERT INTO events (event_id, date, start_time, end_time, title) VALUES (?, ?, ?, ?, ?)",
                        (str(event_id), str(date), str(start_time), str(end_time), str(title)))
        self.conn.commit()

    def get_next_alarm(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events WHERE date >= ? ORDER BY date, start_time LIMIT 1",
                       (datetime.now().strftime('%Y-%m-%d'),))
        row = cursor.fetchone()
        if row:
            event_id, date, start_time, end_time, title = row
            return {
                'event_id': event_id,
                'date': date,
                'start_time': start_time,
                'end_time': end_time,
                'title': title
            }
        else:
            return None

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    # Example usage
    events = [
    ]

    db_file = 'events.db'
    manager = sqlManager(db_file)
    manager.store_alarms(events)
    next_alarm = manager.get_next_alarm()
    print("Next alarm:", next_alarm)
    manager.close()
