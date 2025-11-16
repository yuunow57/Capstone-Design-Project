import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="mysql123",  # ← 너의 비밀번호 맞게 수정
                database="solar_db",
                autocommit=True
            )
            print("✅ MySQL 연결 성공")
        except Error as e:
            print(f"❌ DB 연결 실패: {e}")
            self.conn = None

    def execute(self, query, params=None):
        """INSERT, UPDATE, DELETE용"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            return cursor.rowcount
        except Error as e:
            print(f"❌ SQL 실행 오류: {e}")
            return None

    def fetchall(self, query, params=None):
        """SELECT 여러개"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"❌ SQL 조회 오류: {e}")
            return None

    def fetchone(self, query, params=None):
        """SELECT 한개"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            print(f"❌ SQL 조회 오류: {e}")
            return None


# 싱글톤처럼 전역 인스턴스로 사용
db = Database()
