from flask import Flask, jsonify, render_template_string, request
import psycopg2
import cv2
import numpy as np
import base64
from datetime import datetime

from face_engine import detect_faces, known_faces


app = Flask(__name__)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="face_attendance",
        user="postgres",
        password="Postgres@123",
        port="5432"
    )


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def home():

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Smart Attendance System</title>

<style>

* {
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f2f4f7;
    margin: 0;
}

.header {
    background: #1f4e79;
    color: white;
    padding: 28px 20px;
    text-align: center;
}

.header h1 {
    margin: 0;
    font-size: 28px;
}

.header p {
    margin-bottom: 0;
    opacity: 0.9;
}

.container {
    max-width: 800px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}

.card h2 {
    margin-top: 0;
}

.info {
    color: #666;
    line-height: 1.5;
}

.button {
    width: 100%;
    padding: 15px;
    margin-top: 10px;
    border: none;
    border-radius: 10px;
    background: #1f4e79;
    color: white;
    font-size: 17px;
    cursor: pointer;
}

.button:hover {
    background: #163a5c;
}

.camera {
    background: #198754;
}

.students {
    background: #6f42c1;
}

</style>

</head>

<body>

<div class="header">

<h1>Smart Attendance System</h1>

<p>AI Face Recognition Based Attendance</p>

</div>


<div class="container">


<div class="card">

<h2>📷 Face Attendance</h2>

<p class="info">
Use AI face recognition to automatically identify students
and mark their attendance.
</p>

<button
class="button camera"
onclick="location.href='/attendance-page'">

Start Attendance

</button>

</div>


<div class="card">

<h2>📊 Attendance Dashboard</h2>

<p class="info">
View student attendance records with date, time and status.
</p>

<button
class="button"
onclick="location.href='/attendance'">

View Attendance

</button>

</div>


<div class="card">

<h2>👥 Students</h2>

<p class="info">
View all registered students in the system.
</p>

<button
class="button students"
onclick="location.href='/students'">

View Students

</button>

</div>


</div>

</body>

</html>
""")


# =========================================================
# ATTENDANCE CAMERA PAGE
# =========================================================

@app.route("/attendance-page")
def attendance_page():

    return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Face Attendance</title>

<style>

* {
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    text-align: center;
    background: #f2f4f7;
    padding: 15px;
    margin: 0;
}

.container {
    max-width: 600px;
    margin: auto;
}

video {
    width: 100%;
    max-width: 500px;
    border-radius: 15px;
    background: black;
    margin-top: 10px;
}

canvas {
    display: none;
}

button {
    width: 100%;
    max-width: 500px;
    padding: 15px;
    margin-top: 12px;
    border: none;
    border-radius: 10px;
    background: #1f4e79;
    color: white;
    font-size: 18px;
}

.stop {
    background: #b52b27;
}

.back {
    background: #555;
}

#result {
    margin: 20px auto;
    max-width: 500px;
    padding: 15px;
    border-radius: 10px;
    background: white;
    font-size: 18px;
    font-weight: bold;
}

</style>

</head>


<body>

<div class="container">

<h1>📷 Face Attendance</h1>

<p>
Camera start chesi face ni camera mundu pettandi.
</p>


<video
id="camera"
autoplay
playsinline>
</video>


<canvas id="canvas"></canvas>


<button onclick="startCamera()">
Start Camera
</button>


<button
class="stop"
onclick="stopCamera()">

Stop Camera

</button>


<button
class="back"
onclick="location.href='/'">

Back to Dashboard

</button>


<div id="result">
Waiting for camera...
</div>

</div>


<script>

let stream = null;
let timer = null;
let processing = false;


async function startCamera() {

    try {

        if (stream) {
            return;
        }

        stream = await navigator.mediaDevices.getUserMedia({

            video: {
                facingMode: "user"
            },

            audio: false

        });


        document.getElementById("camera").srcObject = stream;


        document.getElementById("result").innerText =
            "Camera started. Face ni camera mundu pettandi...";


        if (timer) {
            clearInterval(timer);
        }


        timer = setInterval(
            captureFrame,
            1500
        );

    }

    catch(error) {

        console.log(error);

        document.getElementById("result").innerText =
            "Camera permission required.";

        alert(
            "Camera permission allow cheyyandi."
        );

    }

}


function stopCamera() {

    if (timer) {

        clearInterval(timer);

        timer = null;

    }


    if (stream) {

        stream.getTracks().forEach(
            track => track.stop()
        );

        stream = null;

    }


    document.getElementById("camera").srcObject = null;


    document.getElementById("result").innerText =
        "Camera stopped.";

}


async function captureFrame() {

    if (processing) {
        return;
    }


    const video =
        document.getElementById("camera");


    if (
        video.readyState !==
        video.HAVE_ENOUGH_DATA
    ) {

        return;

    }


    processing = true;


    const canvas =
        document.getElementById("canvas");


    canvas.width =
        video.videoWidth;


    canvas.height =
        video.videoHeight;


    const context =
        canvas.getContext("2d");


    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );


    const imageData =
        canvas.toDataURL(
            "image/jpeg",
            0.8
        );


    try {

        const response =
            await fetch(
                "/recognize",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        image: imageData
                    })

                }
            );


        const data =
            await response.json();


        if (data.status === "success") {

            document.getElementById(
                "result"
            ).innerText =
                "✅ " + data.message;

        }

        else if (data.status === "unknown") {

            document.getElementById(
                "result"
            ).innerText =
                "❌ Unknown face";

        }

        else if (data.status === "no_face") {

            document.getElementById(
                "result"
            ).innerText =
                "👤 Face not detected";

        }

        else {

            document.getElementById(
                "result"
            ).innerText =
                "⚠️ " + data.message;

        }

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerText =
            "Server error.";

    }


    processing = false;

}

</script>

</body>

</html>
""")


# =========================================================
# FACE RECOGNITION API
# =========================================================

@app.route("/recognize", methods=["POST"])
def recognize():

    connection = None
    cursor = None

    try:

        data = request.get_json()


        if not data or "image" not in data:

            return jsonify({
                "status": "error",
                "message": "Image not received"
            })


        image_data = data["image"]


        if "," in image_data:

            image_data = image_data.split(
                ",",
                1
            )[1]


        image_bytes = base64.b64decode(
            image_data
        )


        np_array = np.frombuffer(
            image_bytes,
            np.uint8
        )


        frame = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )


        if frame is None:

            return jsonify({
                "status": "error",
                "message": "Invalid image"
            })


        # =====================================================
        # FACE DETECTION
        # =====================================================

        faces = detect_faces(frame)


        if len(faces) == 0:

            return jsonify({
                "status": "no_face",
                "message": "Face not detected"
            })


        # =====================================================
        # SELECT LARGEST FACE
        # =====================================================

        face = max(
            faces,
            key=lambda f:
            (f.bbox[2] - f.bbox[0]) *
            (f.bbox[3] - f.bbox[1])
        )


        current_embedding = face.embedding


        best_name = "Unknown"

        best_score = 0.0


        # =====================================================
        # FACE COMPARISON
        # =====================================================

        for known_name, known_embedding in known_faces.items():

            score = np.dot(
                current_embedding,
                known_embedding
            ) / (
                np.linalg.norm(current_embedding)
                *
                np.linalg.norm(known_embedding)
            )


            if score > best_score:

                best_score = score

                best_name = known_name


        print(
            "Recognized:",
            best_name,
            "Score:",
            best_score
        )


        # =====================================================
        # RECOGNITION THRESHOLD
        # =====================================================

        if best_score < 0.50:

            return jsonify({

                "status": "unknown",

                "message": "Unknown face",

                "score":
                    round(
                        float(best_score),
                        3
                    )

            })


        # =====================================================
        # DATABASE
        # =====================================================

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute("""
            SELECT
                student_id,
                student_name
            FROM students
            WHERE LOWER(student_name)
                = LOWER(%s)
            LIMIT 1
        """, (best_name,))


        student = cursor.fetchone()


        if student is None:

            return jsonify({

                "status": "error",

                "message":
                    f"{best_name} database lo student ga ledu"

            })


        student_id = student[0]

        student_name = student[1]


        # =====================================================
        # CHECK TODAY ATTENDANCE
        # =====================================================

        today = datetime.now().date()


        cursor.execute("""
            SELECT attendance_id
            FROM attendance
            WHERE student_id = %s
            AND attendance_date = %s
            LIMIT 1
        """, (
            student_id,
            today
        ))


        # IMPORTANT: Only ONE fetchone()
        already_marked = cursor.fetchone()


        if already_marked is not None:

            return jsonify({

                "status": "success",

                "message":
                    f"{student_name} attendance already marked today",

                "student":
                    student_name,

                "score":
                    round(
                        float(best_score),
                        3
                    )

            })


        # =====================================================
        # INSERT ATTENDANCE
        # =====================================================

        current_time = datetime.now().time()


        cursor.execute("""
            INSERT INTO attendance
            (
                student_id,
                attendance_date,
                attendance_time,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
        """, (
            student_id,
            today,
            current_time,
            "Present"
        ))


        connection.commit()


        return jsonify({

            "status": "success",

            "message":
                f"Attendance marked for {student_name}",

            "student":
                student_name,

            "score":
                round(
                    float(best_score),
                    3
                )

        })


    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "ERROR:",
            e
        )


        return jsonify({

            "status": "error",

            "message":
                str(e)

        })


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# STUDENTS API
# =========================================================

@app.route("/api/students")
def students_api():

    try:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute("""
            SELECT
                student_id,
                student_name,
                roll_number,
                email
            FROM students
            ORDER BY student_id
        """)


        records = cursor.fetchall()


        cursor.close()

        connection.close()


        students_list = []


        for record in records:

            students_list.append({

                "student_id":
                    record[0],

                "student_name":
                    record[1],

                "roll_number":
                    record[2],

                "email":
                    record[3]

            })


        return jsonify(
            students_list
        )


    except Exception as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        })


# =========================================================
# STUDENTS PAGE
# =========================================================

@app.route("/students")
def students():

    try:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute("""
            SELECT
                student_id,
                student_name,
                roll_number,
                email
            FROM students
            ORDER BY student_id
        """)


        records = cursor.fetchall()


        cursor.close()

        connection.close()


        return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Students</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #f2f4f7;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 900px;
    margin: auto;
}

h1 {
    text-align: center;
}

.card {
    background: white;
    padding: 18px;
    margin-bottom: 12px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.name {
    font-size: 20px;
    font-weight: bold;
    color: #1f4e79;
}

.info {
    color: #555;
    margin-top: 6px;
}

.button {
    width: 100%;
    padding: 14px;
    margin-top: 20px;
    border: none;
    border-radius: 10px;
    background: #1f4e79;
    color: white;
    font-size: 17px;
}

</style>

</head>

<body>

<div class="container">

<h1>👥 Registered Students</h1>

{% for student in records %}

<div class="card">

<div class="name">
{{ student[1] }}
</div>

<div class="info">
Student ID: {{ student[0] }}
</div>

<div class="info">
Roll Number: {{ student[2] }}
</div>

<div class="info">
Email: {{ student[3] }}
</div>

</div>

{% endfor %}


{% if not records %}

<div class="card">
No students found.
</div>

{% endif %}


<button
class="button"
onclick="location.href='/'">

Back to Dashboard

</button>

</div>

</body>

</html>
""", records=records)


    except Exception as e:

        return f"""
        <h2>Database Error</h2>
        <p>{e}</p>
        """


# =========================================================
# ATTENDANCE API
# =========================================================

@app.route("/api/attendance")
def attendance_api():

    try:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute("""
            SELECT
                s.student_name,
                a.attendance_date,
                a.attendance_time,
                a.status
            FROM attendance a
            JOIN students s
            ON a.student_id = s.student_id
            ORDER BY
                a.attendance_date DESC,
                a.attendance_time DESC
        """)


        records = cursor.fetchall()


        cursor.close()

        connection.close()


        attendance_list = []


        for record in records:

            attendance_list.append({

                "student_name":
                    record[0],

                "date":
                    str(record[1]),

                "time":
                    str(record[2]),

                "status":
                    record[3]

            })


        return jsonify(
            attendance_list
        )


    except Exception as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        })


# =========================================================
# PROFESSIONAL ATTENDANCE DASHBOARD
# =========================================================

@app.route("/attendance")
def attendance():

    try:

        connection = get_connection()

        cursor = connection.cursor()


        # -------------------------------------------------
        # ALL ATTENDANCE
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                s.student_name,
                s.roll_number,
                a.attendance_date,
                a.attendance_time,
                a.status
            FROM attendance a
            JOIN students s
            ON a.student_id = s.student_id
            ORDER BY
                a.attendance_date DESC,
                a.attendance_time DESC
        """)


        records = cursor.fetchall()


        # -------------------------------------------------
        # TOTAL STUDENTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM students
        """)


        total_students = cursor.fetchone()[0]


        # -------------------------------------------------
        # TODAY PRESENT
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM attendance
            WHERE attendance_date = CURRENT_DATE
            AND status = 'Present'
        """)


        today_present = cursor.fetchone()[0]


        cursor.close()

        connection.close()


        # -------------------------------------------------
        # CALCULATE ABSENT
        # -------------------------------------------------

        today_absent = (
            total_students -
            today_present
        )


        return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Attendance Dashboard</title>

<style>

* {
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f2f4f7;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1100px;
    margin: auto;
}

.header {
    background: #1f4e79;
    color: white;
    padding: 25px;
    border-radius: 15px;
    text-align: center;
}

.header h1 {
    margin: 0;
}

.header p {
    margin-bottom: 0;
}

.stats {
    display: grid;
    grid-template-columns:
        repeat(3, 1fr);

    gap: 15px;

    margin-top: 20px;
}

.stat {
    background: white;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    box-shadow:
        0 3px 10px
        rgba(0,0,0,0.08);
}

.stat-number {
    font-size: 32px;
    font-weight: bold;
    color: #1f4e79;
}

.stat-title {
    color: #666;
    margin-top: 8px;
}

.table-card {
    background: white;
    margin-top: 20px;
    border-radius: 15px;
    padding: 20px;
    overflow-x: auto;
    box-shadow:
        0 3px 10px
        rgba(0,0,0,0.08);
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background: #1f4e79;
    color: white;
    padding: 13px;
    text-align: left;
}

td {
    padding: 13px;
    border-bottom:
        1px solid #ddd;
}

tr:hover {
    background: #f5f7fa;
}

.present {
    color: #198754;
    font-weight: bold;
}

.empty {
    text-align: center;
    padding: 30px;
    color: #777;
}

.button {
    width: 100%;
    padding: 15px;
    margin-top: 20px;
    border: none;
    border-radius: 10px;
    background: #1f4e79;
    color: white;
    font-size: 17px;
}

@media(max-width: 700px) {

    .stats {
        grid-template-columns: 1fr;
    }

    table {
        min-width: 650px;
    }

}

</style>

</head>


<body>

<div class="container">


<div class="header">

<h1>📊 Attendance Dashboard</h1>

<p>Smart Attendance System</p>

</div>


<div class="stats">


<div class="stat">

<div class="stat-number">
{{ total_students }}
</div>

<div class="stat-title">
Total Students
</div>

</div>


<div class="stat">

<div class="stat-number">
{{ today_present }}
</div>

<div class="stat-title">
Present Today
</div>

</div>


<div class="stat">

<div class="stat-number">
{{ today_absent }}
</div>

<div class="stat-title">
Absent Today
</div>

</div>


</div>


<div class="table-card">

<h2>Attendance Records</h2>


{% if records %}

<table>

<thead>

<tr>

<th>Student Name</th>

<th>Roll Number</th>

<th>Date</th>

<th>Time</th>

<th>Status</th>

</tr>

</thead>


<tbody>

{% for record in records %}

<tr>

<td>
{{ record[0] }}
</td>

<td>
{{ record[1] }}
</td>

<td>
{{ record[2] }}
</td>

<td>
{{ record[3] }}
</td>

<td class="present">
{{ record[4] }}
</td>

</tr>

{% endfor %}

</tbody>

</table>


{% else %}

<div class="empty">

No attendance records found.

</div>

{% endif %}


</div>


<button
class="button"
onclick="location.href='/'">

⬅ Back to Dashboard

</button>


</div>

</body>

</html>

""",

        records=records,

        total_students=total_students,

        today_present=today_present,

        today_absent=today_absent
)


    except Exception as e:

        return f"""
        <h2>Attendance Dashboard Error</h2>
        <p>{e}</p>
        """


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        ssl_context=(
            "10.29.53.2+2.pem",
            "10.29.53.2+2-key.pem"
        )
    )