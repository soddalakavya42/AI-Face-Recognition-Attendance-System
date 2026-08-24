import psycopg2

try:
    connection = psycopg2.connect(
        host="localhost",
        database="face_attendance",
        user="postgres",
        password="Postgres@123",
        port="5432"
    )

    print("Database connected successfully!")

    connection.close()

except Exception as e:
    print("Database connection failed:")
    print(e)