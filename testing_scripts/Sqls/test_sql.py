import sqlite3
import pandas as pd


if __name__ == "__main__":
    conn = sqlite3.connect('/home/ntgroup/Project/rat_vr_small.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM unity_frame")
    df = cursor.fetchall()
    conn.close()
