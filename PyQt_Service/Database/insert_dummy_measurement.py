import mysql.connector
from datetime import datetime, timedelta
import random

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="mysql123",
    database="solar_db"
)

cur = conn.cursor()

start = datetime.now() - timedelta(days=7)

rows = []
current = start

while current <= datetime.now():
    solar_v = round(random.uniform(18.0, 28.0), 2)  # 18~28V
    solar_i = round(random.uniform(0.2, 2.0), 3)   # 0.2~2.0A
    solar_p = round(solar_v * solar_i, 2)

    rows.append((current, solar_v, solar_i, solar_p))
    current += timedelta(minutes=1)  # 1분 간격

sql = """
INSERT INTO measurement (ts, solar_v, solar_i, solar_p)
VALUES (%s, %s, %s, %s)
"""

cur.executemany(sql, rows)
conn.commit()

print(f"✅ {len(rows)}개의 더미 데이터 삽입 완료")
