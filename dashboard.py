import tkinter as tk
from tkinter import ttk
from datetime import date
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
# WINDOW
# =========================

root = tk.Tk()
root.title("AI Face Attendance Dashboard")
root.geometry("1000x700")


# =========================
# TITLE
# =========================

title = tk.Label(
    root,
    text="AI Face Attendance System",
    font=("Arial", 24, "bold")
)

title.pack(pady=15)


subtitle = tk.Label(
    root,
    text="Attendance Dashboard",
    font=("Arial", 14)
)

subtitle.pack(pady=5)


# =========================
# SUMMARY FRAME
# =========================

summary_frame = tk.Frame(root)
summary_frame.pack(pady=15)


# Total Students

total_students_label = tk.Label(
    summary_frame,
    text="Total Students: 0",
    font=("Arial", 14, "bold")
)

total_students_label.pack(
    side=tk.LEFT,
    padx=30
)


# Present Today

today_label = tk.Label(
    summary_frame,
    text="Present Today: 0",
    font=("Arial", 14, "bold")
)

today_label.pack(
    side=tk.LEFT,
    padx=30
)


# Total Attendance

count_label = tk.Label(
    summary_frame,
    text="Total Attendance: 0",
    font=("Arial", 14, "bold")
)

count_label.pack(
    side=tk.LEFT,
    padx=30
)


# =========================
# DATE FILTER
# =========================

filter_frame = tk.Frame(root)
filter_frame.pack(pady=10)


date_text = tk.Label(
    filter_frame,
    text="Date (YYYY-MM-DD):",
    font=("Arial", 11)
)

date_text.pack(
    side=tk.LEFT,
    padx=5
)


date_entry = tk.Entry(
    filter_frame,
    width=15,
    font=("Arial", 11)
)

date_entry.pack(
    side=tk.LEFT,
    padx=5
)

date_entry.insert(
    0,
    str(date.today())
)


# =========================
# TABLE
# =========================

columns = (
    "Student Name",
    "Date",
    "Time",
    "Status"
)

table = ttk.Treeview(
    root,
    columns=columns,
    show="headings"
)


for column in columns:

    table.heading(
        column,
        text=column
    )

    table.column(
        column,
        width=200
    )


table.pack(
    fill=tk.BOTH,
    expand=True,
    padx=20,
    pady=15
)


# =========================
# LOAD DASHBOARD
# =========================

def load_dashboard():

    # Clear table

    for item in table.get_children():

        table.delete(item)


    # Selected date

    selected_date = date_entry.get().strip()


    try:

        filter_date = date.fromisoformat(
            selected_date
        )

    except ValueError:

        status_label.config(
            text="Invalid date. Use YYYY-MM-DD."
        )

        return


    # =========================
    # TOTAL STUDENTS
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM students
        """
    )

    total_students = cursor.fetchone()[0]


    total_students_label.config(
        text=f"Total Students: {total_students}"
    )


    # =========================
    # TOTAL ATTENDANCE
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        """
    )

    total_attendance = cursor.fetchone()[0]


    count_label.config(
        text=f"Total Attendance: {total_attendance}"
    )


    # =========================
    # PRESENT TODAY
    # =========================

    today = date.today()


    cursor.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE attendance_date = %s
        """,
        (today,)
    )

    present_today = cursor.fetchone()[0]


    today_label.config(
        text=f"Present Today: {present_today}"
    )


    # =========================
    # DATE-WISE ATTENDANCE
    # =========================

    cursor.execute(
        """
        SELECT
            s.student_name,
            a.attendance_date,
            a.attendance_time,
            a.status

        FROM attendance a

        JOIN students s
        ON a.student_id = s.student_id

        WHERE a.attendance_date = %s

        ORDER BY a.attendance_time DESC
        """,
        (filter_date,)
    )


    records = cursor.fetchall()


    for record in records:

        table.insert(
            "",
            tk.END,
            values=record
        )


    status_label.config(
        text=f"Showing attendance for {filter_date}"
    )


# =========================
# BUTTONS
# =========================

button_frame = tk.Frame(root)
button_frame.pack(pady=5)


search_button = tk.Button(
    button_frame,
    text="Search Date",
    command=load_dashboard,
    font=("Arial", 11)
)

search_button.pack(
    side=tk.LEFT,
    padx=10
)


refresh_button = tk.Button(
    button_frame,
    text="Refresh",
    command=load_dashboard,
    font=("Arial", 11)
)

refresh_button.pack(
    side=tk.LEFT,
    padx=10
)


# =========================
# STATUS
# =========================

status_label = tk.Label(
    root,
    text="",
    font=("Arial", 10)
)

status_label.pack(
    pady=5
)


# =========================
# START
# =========================

load_dashboard()

root.mainloop()


# =========================
# CLEANUP
# =========================

cursor.close()
connection.close()