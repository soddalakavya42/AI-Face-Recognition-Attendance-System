import csv
import psycopg2


# =========================
# DATABASE CONNECTION
# =========================

connection = psycopg2.connect(
    host="localhost",
    database="face_attendance",
    user="postgres",
    password="Postgres@123",
    port="5432"
)

cursor = connection.cursor()


# =========================
# FETCH ATTENDANCE
# =========================

cursor.execute(
    """
    SELECT
        s.student_name,
        s.roll_number,
        a.attendance_date,
        a.attendance_time,
        a.status
    FROM attendance a
    JOIN students s
    ON a.student_id = s.student_id
    ORDER BY a.attendance_date DESC,
             a.attendance_time DESC
    """
)

records = cursor.fetchall()


# =========================
# CREATE CSV REPORT
# =========================

file_name = "attendance_report.csv"

with open(
    file_name,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow(
        [
            "Student Name",
            "Roll Number",
            "Attendance Date",
            "Attendance Time",
            "Status"
        ]
    )

    writer.writerows(records)


# =========================
# RESULT
# =========================

print("Attendance report generated successfully!")

print(
    f"Total records exported: {len(records)}"
)

print(
    f"File name: {file_name}"
)


# =========================
# CLEANUP
# =========================

cursor.close()

connection.close()