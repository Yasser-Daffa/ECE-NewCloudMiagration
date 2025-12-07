# test_connection.py
import psycopg2

def test_connection():
    try:
        con = psycopg2.connect(
            host="shuttle.proxy.rlwy.net",
            port=36230,
            database="railway",
            user="postgres",
            password="GeFRnoAfOOBgqUuTxgtvFnbKMVAYkjSO"
        )

        cur = con.cursor()
        cur.execute("SELECT NOW();")  # simple query
        server_time = cur.fetchone()

        print("=====================================")
        print("   Connection to PostgreSQL SUCCESS ")
        print("   Server Time:", server_time)
        print("=====================================")

        cur.close()
        con.close()

    except Exception as e:
        print(" CONNECTION FAILED!")
        print("Error:", e)

if __name__ == "__main__":
    test_connection()
