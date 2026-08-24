import cv2
import psycopg2
from datetime import datetime
import numpy as np

from face_engine import detect_faces, draw_faces, known_faces


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

print("Database connected successfully!")


# =========================
# SAVE FACE ENCODINGS
# =========================

for name, embedding in known_faces.items():

    encoding_text = ",".join(map(str, embedding.tolist()))

    cursor.execute(
        """
        UPDATE students
        SET face_encoding = %s
        WHERE LOWER(student_name) = LOWER(%s)
        """,
        (encoding_text, name)
    )

connection.commit()

print("Face encodings saved to database!")


# =========================
# MARK ATTENDANCE
# =========================

def mark_attendance(student_name):

    try:

        cursor.execute(
            """
            SELECT student_id
            FROM students
            WHERE LOWER(student_name) = LOWER(%s)
            """,
            (student_name,)
        )

        student = cursor.fetchone()

        if student is None:

            print(f"Student '{student_name}' not found in database.")

            return False


        student_id = student[0]

        today = datetime.now().date()
        current_time = datetime.now().time()


        # Check if attendance already exists today

        cursor.execute(
            """
            SELECT attendance_id
            FROM attendance
            WHERE student_id = %s
            AND attendance_date = %s
            """,
            (student_id, today)
        )

        existing = cursor.fetchone()


        if existing:

            return False


        # Insert attendance

        cursor.execute(
            """
            INSERT INTO attendance
            (
                student_id,
                attendance_date,
                attendance_time,
                status
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                student_id,
                today,
                current_time,
                "Present"
            )
        )

        connection.commit()

        print(f"Attendance marked for {student_name}")

        return True


    except Exception as e:

        connection.rollback()

        print("Attendance error:")
        print(e)

        return False


# =========================
# CAMERA
# =========================

camera = cv2.VideoCapture(0)


if not camera.isOpened():

    print("Camera could not be opened.")

    cursor.close()
    connection.close()

    exit()


print("Camera started. Press Q to quit.")


# =========================
# MAIN LOOP
# =========================

while True:

    success, frame = camera.read()


    if not success:

        print("Failed to read camera.")

        break


    # Detect faces

    faces = detect_faces(frame)


    # Draw face boxes

    frame = draw_faces(frame, faces)


    # =========================
    # FACE RECOGNITION
    # =========================

    for face in faces:

        name = "Unknown"

        best_score = 0

        if known_faces:

            current_embedding = face.embedding

            best_name = "Unknown"


            for known_name, known_embedding in known_faces.items():

                score = np.dot(
                    current_embedding,
                    known_embedding
                ) / (
                    np.linalg.norm(current_embedding)
                    * np.linalg.norm(known_embedding)
                )


                if score > best_score:

                    best_score = score
                    best_name = known_name


            # Recognition threshold

            if best_score > 0.45:

                name = best_name


        # =========================
        # RECOGNIZED FACE
        # =========================

        if name != "Unknown":

            attendance_marked = mark_attendance(name)


            # Display recognized name

            cv2.putText(
                frame,
                f"Recognized: {name}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )


            # Display attendance status

            if attendance_marked:

                status_text = "Attendance Marked"

            else:

                status_text = "Attendance Already Marked"


            cv2.putText(
                frame,
                status_text,
                (50, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )


        # =========================
        # UNKNOWN FACE
        # =========================

        else:

            cv2.putText(
                frame,
                "Unknown",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )


    # =========================
    # SHOW CAMERA
    # =========================

    cv2.imshow(
        "AI Attendance System",
        frame
    )


    # Press Q to quit

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# =========================
# CLEANUP
# =========================

camera.release()

cv2.destroyAllWindows()

cursor.close()

connection.close()

print("Application closed.")