import tkinter as tk
from tkinter import ttk
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

root.title("Student Management")
root.geometry("800x550")


# =========================
# TITLE
# =========================

title = tk.Label(
    root,
    text="Student Management",
    font=("Arial", 22, "bold")
)

title.pack(pady=20)


# =========================
# TABLE
# =========================

columns = (
    "Student ID",
    "Student Name",
    "Roll Number",
    "Email"
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
        width=180
    )


table.pack(
    fill=tk.BOTH,
    expand=True,
    padx=20,
    pady=20
)


# =========================
# LOAD STUDENTS
# =========================

def load_students():

    for item in table.get_children():
        table.delete(item)

    cursor.execute(
        """
        SELECT
            student_id,
            student_name,
            roll_number,
            email
        FROM students
        ORDER BY student_id
        """
    )

    students = cursor.fetchall()

    for student in students:

        table.insert(
            "",
            tk.END,
            values=student
        )


# =========================
# REFRESH BUTTON
# =========================

refresh_button = tk.Button(
    root,
    text="Refresh Students",
    command=load_students,
    font=("Arial", 12)
)

refresh_button.pack(pady=15)


# =========================
# START
# =========================

load_students()

root.mainloop()


# =========================
# CLEANUP
# =========================

cursor.close()
connection.close()