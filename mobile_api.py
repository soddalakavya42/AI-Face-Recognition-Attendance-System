from flask import Flask, jsonify, render_template_string, request, Response, session, redirect
import psycopg2
import cv2
import numpy as np
import base64
import csv
import re
import os
from io import StringIO
from datetime import datetime

from face_engine import detect_faces, known_faces, register_face


app = Flask(__name__)

app.secret_key = "smart-attendance-secret-key"


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL")
    )


# =========================================================
# HELPER - SAFE FACE FILE NAME
# =========================================================

def safe_face_name(name):

    return (
        name.strip()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "admin" and password == "admin123":

            session["logged_in"] = True

            return redirect("/")

        return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Login</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f2f4f7;
}

.container {
    max-width: 400px;
    margin: 80px auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 30px;
    border-radius: 18px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.10);
}

h1 {
    text-align: center;
    color: #1f4e79;
}

.subtitle {
    text-align: center;
    color: #666;
}

.error {
    background: #f8d7da;
    color: #842029;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
    text-align: center;
}

input {
    width: 100%;
    padding: 14px;
    margin: 8px 0 15px;
    border: 1px solid #ccc;
    border-radius: 9px;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 9px;
    background: #1f4e79;
    color: white;
    font-size: 17px;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>🔐 Admin Login</h1>

<p class="subtitle">
AI Face Recognition Attendance
</p>

<div class="error">
Invalid username or password
</div>

<form method="POST">

<input
name="username"
placeholder="Username"
required
>

<input
name="password"
type="password"
placeholder="Password"
required
>

<button type="submit">
Login
</button>

</form>

</div>

</div>

</body>

</html>
""")

    return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Login</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f2f4f7;
}

.container {
    max-width: 400px;
    margin: 80px auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 30px;
    border-radius: 18px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.10);
}

h1 {
    text-align: center;
    color: #1f4e79;
}

.subtitle {
    text-align: center;
    color: #666;
}

input {
    width: 100%;
    padding: 14px;
    margin: 8px 0 15px;
    border: 1px solid #ccc;
    border-radius: 9px;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 9px;
    background: #1f4e79;
    color: white;
    font-size: 17px;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>🔐 Admin Login</h1>

<p class="subtitle">
AI Face Recognition Attendance System
</p>

<form method="POST">

<input
name="username"
placeholder="Username"
required
>

<input
name="password"
type="password"
placeholder="Password"
required
>

<button type="submit">
Login
</button>

</form>

</div>

</div>

</body>

</html>
""")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# LOGIN CHECK
# =========================================================

def login_required():

    return session.get("logged_in") is True


# =========================================================
# MAIN DASHBOARD
# =========================================================

@app.route("/")
def dashboard():

    if not login_required():

        return redirect("/login")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM students
        """)

        total_students = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM attendance
            WHERE attendance_date = CURRENT_DATE
            AND status = 'Present'
        """)

        today_present = cursor.fetchone()[0]

        today_absent = total_students - today_present

        return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>AI Attendance Dashboard</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f2f4f7;
}

.container {
    max-width: 1000px;
    margin: auto;
    padding: 20px;
}

.header {
    background: #1f4e79;
    color: white;
    padding: 25px;
    border-radius: 16px;
    text-align: center;
}

.header h1 {
    margin: 0;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 20px;
}

.stat {
    background: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}

.number {
    font-size: 32px;
    font-weight: bold;
    color: #1f4e79;
}

.label {
    color: #666;
    margin-top: 8px;
}

.actions {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    margin-top: 20px;
}

button {
    border: none;
    border-radius: 12px;
    padding: 18px;
    color: white;
    font-size: 17px;
    cursor: pointer;
}

.attendance {
    background: #198754;
}

.students {
    background: #0d9488;
}

.records {
    background: #6f42c1;
}

.add {
    background: #d97706;
}

.logout {
    background: #dc3545;
}

@media(max-width: 700px) {

    .stats {
        grid-template-columns: 1fr;
    }

    .actions {
        grid-template-columns: 1fr;
    }

}

</style>

</head>

<body>

<div class="container">

<div class="header">

<h1>🤖 AI Face Recognition Attendance</h1>

<p>Smart Attendance System</p>

</div>


<div class="stats">

<div class="stat">

<div class="number">
{{ total_students }}
</div>

<div class="label">
Total Students
</div>

</div>


<div class="stat">

<div class="number">
{{ today_present }}
</div>

<div class="label">
Present Today
</div>

</div>


<div class="stat">

<div class="number">
{{ today_absent }}
</div>

<div class="label">
Absent Today
</div>

</div>

</div>


<div class="actions">

<button
class="attendance"
onclick="location.href='/attendance-page'">

📷 Mark Attendance

</button>


<button
class="students"
onclick="location.href='/students'">

👥 View Students

</button>


<button
class="records"
onclick="location.href='/attendance'">

📊 Attendance Records

</button>


<button
class="add"
onclick="location.href='/add-student'">

➕ Add Student

</button>


<button
class="logout"
onclick="location.href='/logout'">

🚪 Logout

</button>

</div>

</div>

</body>

</html>
""",
            total_students=total_students,
            today_present=today_present,
            today_absent=today_absent
        )

    except Exception as e:

        return f"""
        <h2>Dashboard Error</h2>
        <p>{e}</p>
        """

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ATTENDANCE CAMERA PAGE
# =========================================================

@app.route("/attendance-page")
def attendance_page():

    if not login_required():

        return redirect("/login")

    return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Mark Attendance</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 15px;
    font-family: Arial, sans-serif;
    background: #f2f4f7;
}

.container {
    max-width: 650px;
    margin: auto;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}

h1 {
    text-align: center;
    color: #1f4e79;
}

video {
    width: 100%;
    border-radius: 15px;
    background: black;
    margin-top: 15px;
}

canvas {
    display: none;
}

button {
    width: 100%;
    padding: 15px;
    margin-top: 12px;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 17px;
}

.start {
    background: #198754;
}

.stop {
    background: #dc3545;
}

.back {
    background: #555;
}

#result {
    margin-top: 15px;
    padding: 15px;
    border-radius: 10px;
    background: #f8f9fa;
    text-align: center;
    font-weight: bold;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>📷 Mark Attendance</h1>

<video
id="camera"
autoplay
playsinline>
</video>

<canvas id="canvas"></canvas>

<button
class="start"
onclick="startCamera()">

▶ Start Camera

</button>

<button
class="stop"
onclick="stopCamera()">

⏹ Stop Camera

</button>

<button
class="back"
onclick="location.href='/'">

⬅ Dashboard

</button>

<div id="result">
Camera not started.
</div>

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

        stream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    facingMode: "user"
                },

                audio: false

            });


        document.getElementById(
            "camera"
        ).srcObject = stream;


        document.getElementById(
            "result"
        ).innerHTML =
            "📷 Camera started. Face ni camera mundu pettandi.";


        timer = setInterval(
            captureFrame,
            1500
        );

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Camera permission required.";

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


    document.getElementById(
        "result"
    ).innerHTML =
        "⏹ Camera stopped.";

}


async function captureFrame() {

    if (!stream || processing) {
        return;
    }


    const video =
        document.getElementById(
            "camera"
        );


    if (
        video.videoWidth === 0 ||
        video.videoHeight === 0
    ) {

        return;

    }


    const canvas =
        document.getElementById(
            "canvas"
        );


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


    const image =
        canvas.toDataURL(
            "image/jpeg",
            0.85
        );


    processing = true;


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
                        image: image
                    })

                }
            );


        const data =
            await response.json();


        document.getElementById(
            "result"
        ).innerHTML =
            data.message || "Response received.";


        if (
            data.status === "success"
        ) {

            if (
                data.already_marked === true
            ) {

                document.getElementById(
                    "result"
                ).innerHTML =
                    "⚠️ " + data.message;

            }

            else {

                document.getElementById(
                    "result"
                ).innerHTML =
                    "✅ " + data.message;

            }

        }

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Server error.";

    }

    finally {

        processing = false;

    }

}

</script>

</body>

</html>
""")


# =========================================================
# RECOGNIZE FACE + DAILY ATTENDANCE
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


        faces = detect_faces(frame)


        if len(faces) == 0:

            return jsonify({
                "status": "no_face",
                "message": "Face not detected"
            })


        face = max(
            faces,
            key=lambda f:
                (f.bbox[2] - f.bbox[0])
                *
                (f.bbox[3] - f.bbox[1])
        )


        current_embedding = face.embedding


        best_name = "Unknown"
        best_score = 0


        for known_name, known_embedding in known_faces.items():

            denominator = (
                np.linalg.norm(current_embedding)
                *
                np.linalg.norm(known_embedding)
            )


            if denominator == 0:
                continue


            score = np.dot(
                current_embedding,
                known_embedding
            ) / denominator


            if score > best_score:

                best_score = score
                best_name = known_name


        print(
            "Recognized:",
            best_name,
            "Score:",
            best_score
        )


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


        connection = get_connection()
        cursor = connection.cursor()


        cursor.execute("""
            SELECT
                student_id,
                student_name
            FROM students
            WHERE LOWER(student_name) = LOWER(%s)
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


        # =================================================
        # IMPORTANT:
        # TODAY DATE CHECK
        # =================================================

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


        already_marked = cursor.fetchone()


        # =================================================
        # SAME DAY ALREADY MARKED
        # =================================================

        if already_marked is not None:

            print(
                f"Already marked today: {student_name}"
            )


            return jsonify({

                "status": "success",

                "message":
                    f"Recognized: {student_name} | Attendance already marked today",

                "student":
                    student_name,

                "recognized":
                    True,

                "already_marked":
                    True,

                "score":
                    round(
                        float(best_score),
                        3
                    )

            })


        # =================================================
        # FIRST ATTENDANCE OF TODAY
        # =================================================

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


        print(
            f"Attendance marked for {student_name} on {today}"
        )


        return jsonify({

            "status": "success",

            "message":
                f"Recognized: {student_name} | Attendance marked successfully",

            "student":
                student_name,

            "recognized":
                True,

            "already_marked":
                False,

            "score":
                round(
                    float(best_score),
                    3
                )

        })


    except Exception as e:

        print(
            "RECOGNIZE ERROR:",
            e
        )


        if connection:

            connection.rollback()


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
# ADD STUDENT PAGE
# =========================================================

@app.route("/add-student")
def add_student_page():

    if not login_required():

        return redirect("/login")


    return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Add Student</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 15px;
    font-family: Arial, sans-serif;
    background: #f2f4f7;
}

.container {
    max-width: 600px;
    margin: auto;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}

h1 {
    text-align: center;
    color: #1f4e79;
}

label {
    display: block;
    margin-top: 12px;
    font-weight: bold;
}

input {
    width: 100%;
    padding: 14px;
    margin-top: 7px;
    border: 1px solid #ccc;
    border-radius: 9px;
    font-size: 16px;
}

video {
    width: 100%;
    margin-top: 15px;
    border-radius: 15px;
    background: black;
}

canvas {
    display: none;
}

button {
    width: 100%;
    padding: 15px;
    margin-top: 12px;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 17px;
}

.open {
    background: #198754;
}

.capture {
    background: #0d9488;
}

.save {
    background: #6f42c1;
}

.back {
    background: #555;
}

#result {
    margin-top: 15px;
    padding: 15px;
    border-radius: 10px;
    background: #f8f9fa;
    text-align: center;
    font-weight: bold;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>➕ Add Student</h1>


<label>
Student Name
</label>

<input
id="studentName"
type="text"
placeholder="Enter student name"
>


<label>
Roll Number
</label>

<input
id="rollNumber"
type="text"
placeholder="Enter roll number"
>


<label>
Email
</label>

<input
id="email"
type="email"
placeholder="Enter email"
>


<video
id="camera"
autoplay
playsinline>
</video>

<canvas id="canvas"></canvas>


<button
class="open"
onclick="startCamera()">

📷 Open Camera

</button>


<button
class="capture"
onclick="captureFace()">

📸 Capture Face

</button>


<button
class="save"
onclick="saveStudent()">

💾 Save Student

</button>


<button
class="back"
onclick="location.href='/'">

⬅ Dashboard

</button>


<div id="result">
Camera not started.
</div>

</div>

</div>


<script>

let stream = null;
let capturedImage = null;


async function startCamera() {

    try {

        if (stream) {
            return;
        }


        stream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    facingMode: "user"
                },

                audio: false

            });


        document.getElementById(
            "camera"
        ).srcObject = stream;


        document.getElementById(
            "result"
        ).innerHTML =
            "📷 Camera started. Face ni camera mundu pettandi.";

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Camera permission required.";

    }

}


function captureFace() {

    const video =
        document.getElementById(
            "camera"
        );


    if (!stream) {

        document.getElementById(
            "result"
        ).innerHTML =
            "⚠️ First Open Camera click cheyyandi.";

        return;

    }


    if (
        video.videoWidth === 0 ||
        video.videoHeight === 0
    ) {

        document.getElementById(
            "result"
        ).innerHTML =
            "⚠️ Camera ready avvadaniki wait cheyyandi.";

        return;

    }


    const canvas =
        document.getElementById(
            "canvas"
        );


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


    capturedImage =
        canvas.toDataURL(
            "image/jpeg",
            0.9
        );


    document.getElementById(
        "result"
    ).innerHTML =
        "✅ Face captured. Save Student click cheyyandi.";

}


async function saveStudent() {

    const name =
        document.getElementById(
            "studentName"
        ).value.trim();


    const roll =
        document.getElementById(
            "rollNumber"
        ).value.trim();


    const email =
        document.getElementById(
            "email"
        ).value.trim();


    if (!name) {

        alert(
            "Student name enter cheyyandi."
        );

        return;

    }


    if (!roll) {

        alert(
            "Roll number enter cheyyandi."
        );

        return;

    }


    if (!capturedImage) {

        alert(
            "First face capture cheyyandi."
        );

        return;

    }


    document.getElementById(
        "result"
    ).innerHTML =
        "⏳ Student saving...";


    try {

        const response =
            await fetch(
                "/api/students/add",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        student_name:
                            name,

                        roll_number:
                            roll,

                        email:
                            email,

                        image:
                            capturedImage

                    })

                }
            );


        const data =
            await response.json();


        if (
            data.status === "success"
        ) {

            document.getElementById(
                "result"
            ).innerHTML =
                "✅ " + data.message;


            if (stream) {

                stream.getTracks().forEach(
                    track => track.stop()
                );

                stream = null;

            }


            setTimeout(
                function() {

                    location.href =
                        "/students";

                },
                1200
            );

        }

        else {

            document.getElementById(
                "result"
            ).innerHTML =
                "❌ " + data.message;

        }

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Server error.";

    }

}

</script>

</body>

</html>
""")


# =========================================================
# ADD STUDENT API
# =========================================================

@app.route("/api/students/add", methods=["POST"])
def add_student():

    connection = None
    cursor = None

    try:

        data = request.get_json()


        if not data:

            return jsonify({
                "status": "error",
                "message": "Data not received"
            })


        student_name = data.get(
            "student_name",
            ""
        ).strip()


        roll_number = data.get(
            "roll_number",
            ""
        ).strip()


        email = data.get(
            "email",
            ""
        ).strip()


        image_data = data.get(
            "image",
            ""
        )


        if not student_name:

            return jsonify({
                "status": "error",
                "message": "Student name required"
            })


        if not roll_number:

            return jsonify({
                "status": "error",
                "message": "Roll number required"
            })


        if not image_data:

            return jsonify({
                "status": "error",
                "message": "Face image required"
            })


        if not re.match(
            r"^[A-Za-z0-9 _.-]+$",
            student_name
        ):

            return jsonify({
                "status": "error",
                "message":
                    "Student name contains invalid characters"
            })


        connection = get_connection()
        cursor = connection.cursor()


        cursor.execute("""
            SELECT student_id
            FROM students
            WHERE LOWER(student_name) = LOWER(%s)
            OR LOWER(roll_number) = LOWER(%s)
            LIMIT 1
        """, (
            student_name,
            roll_number
        ))


        existing = cursor.fetchone()


        if existing is not None:

            return jsonify({
                "status": "error",
                "message":
                    "Student name or roll number already exists"
            })


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


        success, result = register_face(
            student_name,
            frame
        )


        if not success:

            return jsonify({
                "status": "error",
                "message": result
            })


        cursor.execute("""
            INSERT INTO students
            (
                student_name,
                roll_number,
                email
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            RETURNING student_id
        """, (
            student_name,
            roll_number,
            email
        ))


        student_id = cursor.fetchone()[0]


        connection.commit()


        print(
            f"Student registered: {student_name}"
        )


        return jsonify({

            "status": "success",

            "message":
                f"Student {student_name} registered successfully",

            "student_id":
                student_id

        })


    except Exception as e:

        print(
            "ADD STUDENT ERROR:",
            e
        )


        if connection:
            connection.rollback()


        return jsonify({
            "status": "error",
            "message": str(e)
        })


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# VIEW STUDENTS
# =========================================================

@app.route("/students")
def students():

    if not login_required():

        return redirect("/login")


    connection = None
    cursor = None

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


        return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Students</title>

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
    max-width: 900px;
    margin: auto;
}

h1 {
    text-align: center;
    color: #1f4e79;
}

.top-button {
    width: 100%;
    padding: 15px;
    margin-bottom: 18px;
    border: none;
    border-radius: 10px;
    background: #0d9488;
    color: white;
    font-size: 17px;
}

.card {
    background: white;
    padding: 18px;
    margin-bottom: 15px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.name {
    font-size: 21px;
    font-weight: bold;
    color: #1f4e79;
}

.info {
    color: #555;
    margin-top: 7px;
}

.buttons {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    margin-top: 15px;
}

.buttons button {
    border: none;
    padding: 12px;
    border-radius: 8px;
    color: white;
    font-size: 15px;
}

.view {
    background: #0d6efd;
}

.edit {
    background: #6f42c1;
}

.delete {
    background: #dc3545;
}

.back {
    width: 100%;
    padding: 14px;
    margin-top: 15px;
    border: none;
    border-radius: 10px;
    background: #555;
    color: white;
    font-size: 17px;
}

.empty {
    background: white;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    color: #777;
}

@media(max-width: 600px) {

    .buttons {
        grid-template-columns: 1fr;
    }

}

</style>

</head>

<body>

<div class="container">

<h1>👥 Registered Students</h1>


<button
class="top-button"
onclick="location.href='/add-student'">

➕ Add Student Using Camera

</button>


{% for student in records %}

<div
class="card"
id="student-{{ student[0] }}"
>

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
Email:
{{ student[3] if student[3] else "Not provided" }}
</div>


<div class="buttons">


<button
class="view"
onclick='viewStudent(
{{ student[0] }},
{{ student[1]|tojson }},
{{ student[2]|tojson }},
{{ (student[3] or "")|tojson }}
)'>

👁️ View

</button>


<button
class="edit"
onclick='editStudent(
{{ student[0] }},
{{ student[1]|tojson }},
{{ student[2]|tojson }},
{{ (student[3] or "")|tojson }}
)'>

✏️ Edit

</button>


<button
class="delete"
onclick='deleteStudent(
{{ student[0] }},
{{ student[1]|tojson }}
)'>

🗑️ Delete

</button>


</div>

</div>

{% endfor %}


{% if not records %}

<div class="empty">

👥 No students registered.

</div>

{% endif %}


<button
class="back"
onclick="location.href='/'">

⬅ Back to Dashboard

</button>

</div>


<script>


function viewStudent(
    id,
    name,
    roll,
    email
) {

    alert(
        "👤 Student Details\\n\\n" +

        "Student ID: " +
        id +

        "\\nStudent Name: " +
        name +

        "\\nRoll Number: " +
        roll +

        "\\nEmail: " +
        (email || "Not provided")
    );

}


function editStudent(
    id,
    name,
    roll,
    email
) {

    location.href =
        "/edit-student/" +
        id;

}


async function deleteStudent(
    studentId,
    studentName
) {

    const confirmed =
        confirm(
            "Are you sure you want to delete " +
            studentName +
            "?\\n\\n" +

            "Student details, attendance records " +
            "and face data will be deleted."
        );


    if (!confirmed) {

        return;

    }


    try {

        const response =
            await fetch(
                "/api/students/delete/" +
                studentId,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (
            data.status === "success"
        ) {

            alert(
                "✅ " +
                data.message
            );


            const card =
                document.getElementById(
                    "student-" +
                    studentId
                );


            if (card) {

                card.remove();

            }


        }

        else {

            alert(
                "❌ Delete failed\\n\\n" +
                data.message
            );

        }

    }

    catch(error) {

        console.log(error);

        alert(
            "❌ Server error while deleting student."
        );

    }

}

</script>

</body>

</html>
""",
            records=records
        )


    except Exception as e:

        return f"""
        <h2>Database Error</h2>
        <p>{e}</p>
        """


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# EDIT STUDENT PAGE
# =========================================================

@app.route(
    "/edit-student/<int:student_id>",
    methods=["GET"]
)
def edit_student_page(student_id):

    if not login_required():

        return redirect("/login")


    connection = None
    cursor = None

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
            WHERE student_id = %s
        """, (student_id,))


        student = cursor.fetchone()


        if student is None:

            return """
            <h2>Student not found</h2>
            <a href="/students">Back</a>
            """


        return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Edit Student</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f2f4f7;
}

.container {
    max-width: 600px;
    margin: auto;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}

h1 {
    color: #1f4e79;
    text-align: center;
}

label {
    display: block;
    margin-top: 15px;
    font-weight: bold;
}

input {
    width: 100%;
    padding: 14px;
    margin-top: 7px;
    border: 1px solid #ccc;
    border-radius: 9px;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 14px;
    margin-top: 15px;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 17px;
}

.save {
    background: #198754;
}

.cancel {
    background: #555;
}

#result {
    margin-top: 15px;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
    font-weight: bold;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>✏️ Edit Student</h1>


<label>
Student Name
</label>

<input
id="studentName"
value="{{ student[1] }}"
>


<label>
Roll Number
</label>

<input
id="rollNumber"
value="{{ student[2] }}"
>


<label>
Email
</label>

<input
id="email"
type="email"
value="{{ student[3] or '' }}"
>


<button
class="save"
onclick="updateStudent()">

💾 Save Changes

</button>


<button
class="cancel"
onclick="location.href='/students'">

⬅ Cancel

</button>


<div id="result"></div>

</div>

</div>


<script>

async function updateStudent() {

    const name =
        document.getElementById(
            "studentName"
        ).value.trim();


    const roll =
        document.getElementById(
            "rollNumber"
        ).value.trim();


    const email =
        document.getElementById(
            "email"
        ).value.trim();


    if (!name) {

        alert(
            "Student name required."
        );

        return;

    }


    if (!roll) {

        alert(
            "Roll number required."
        );

        return;

    }


    document.getElementById(
        "result"
    ).innerHTML =
        "⏳ Updating...";


    try {

        const response =
            await fetch(
                "/api/students/update/{{ student[0] }}",
                {

                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        student_name:
                            name,

                        roll_number:
                            roll,

                        email:
                            email

                    })

                }
            );


        const data =
            await response.json();


        if (
            data.status === "success"
        ) {

            document.getElementById(
                "result"
            ).innerHTML =
                "✅ " + data.message;


            setTimeout(
                function() {

                    location.href =
                        "/students";

                },
                1000
            );

        }

        else {

            document.getElementById(
                "result"
            ).innerHTML =
                "❌ " + data.message;

        }

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Server error.";

    }

}

</script>

</body>

</html>
""",
            student=student
        )


    except Exception as e:

        return f"""
        <h2>Edit Error</h2>
        <p>{e}</p>
        """


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# UPDATE STUDENT API
# =========================================================

@app.route(
    "/api/students/update/<int:student_id>",
    methods=["PUT"]
)
def update_student(student_id):

    connection = None
    cursor = None

    try:

        data = request.get_json()


        if not data:

            return jsonify({
                "status": "error",
                "message": "Data not received"
            })


        new_name = data.get(
            "student_name",
            ""
        ).strip()


        new_roll = data.get(
            "roll_number",
            ""
        ).strip()


        new_email = data.get(
            "email",
            ""
        ).strip()


        if not new_name:

            return jsonify({
                "status": "error",
                "message": "Student name required"
            })


        if not new_roll:

            return jsonify({
                "status": "error",
                "message": "Roll number required"
            })


        if not re.match(
            r"^[A-Za-z0-9 _.-]+$",
            new_name
        ):

            return jsonify({
                "status": "error",
                "message":
                    "Student name contains invalid characters"
            })


        connection = get_connection()
        cursor = connection.cursor()


        # -------------------------------------------------
        # GET OLD DETAILS
        # -------------------------------------------------

        cursor.execute("""
            SELECT student_name
            FROM students
            WHERE student_id = %s
        """, (student_id,))


        old_student = cursor.fetchone()


        if old_student is None:

            return jsonify({
                "status": "error",
                "message": "Student not found"
            })


        old_name = old_student[0]


        # -------------------------------------------------
        # CHECK DUPLICATE NAME / ROLL
        # -------------------------------------------------

        cursor.execute("""
            SELECT student_id
            FROM students
            WHERE
                (
                    LOWER(student_name) = LOWER(%s)
                    OR LOWER(roll_number) = LOWER(%s)
                )
                AND student_id <> %s
            LIMIT 1
        """, (
            new_name,
            new_roll,
            student_id
        ))


        duplicate = cursor.fetchone()


        if duplicate is not None:

            return jsonify({
                "status": "error",
                "message":
                    "Another student already has this name or roll number"
            })


        # -------------------------------------------------
        # UPDATE DATABASE
        # -------------------------------------------------

        cursor.execute("""
            UPDATE students
            SET
                student_name = %s,
                roll_number = %s,
                email = %s
            WHERE student_id = %s
        """, (
            new_name,
            new_roll,
            new_email,
            student_id
        ))


        connection.commit()


        # -------------------------------------------------
        # UPDATE FACE MEMORY IF NAME CHANGED
        # -------------------------------------------------

        old_safe_name = safe_face_name(old_name)

        new_safe_name = safe_face_name(new_name)


        if old_safe_name != new_safe_name:

            # Update known_faces dictionary
            if old_safe_name in known_faces:

                known_faces[new_safe_name] = known_faces.pop(old_safe_name)


            # Rename face image
            old_image = os.path.join(
                    "known_faces",
                    old_safe_name + ".jpg"
                )


            new_image = os.path.join(
                    "known_faces",
                    new_safe_name + ".jpg"
                )


            if os.path.exists(old_image):

                try:

                    os.rename(
                        old_image,
                        new_image
                    )

                    print(
                        f"Face image renamed: "
                        f"{old_image} -> {new_image}"
                    )

                except Exception as image_error:

                    print(
                        "IMAGE RENAME ERROR:",
                        image_error
                    )


        print(
            f"Student updated: "
            f"{old_name} -> {new_name}"
        )


        return jsonify({

            "status": "success",

            "message":
                f"Student {new_name} updated successfully"

        })


    except Exception as e:

        print(
            "UPDATE STUDENT ERROR:",
            e
        )


        if connection:

            connection.rollback()


        return jsonify({

            "status": "error",

            "message": str(e)

        })


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE STUDENT API
# =========================================================

@app.route(
    "/api/students/delete/<int:student_id>",
    methods=["DELETE"]
)
def delete_student(student_id):

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()


        # -------------------------------------------------
        # FIND STUDENT
        # -------------------------------------------------

        cursor.execute("""
            SELECT student_name
            FROM students
            WHERE student_id = %s
        """, (student_id,))


        student = cursor.fetchone()


        if student is None:

            return jsonify({

                "status": "error",

                "message":
                    "Student not found"

            })


        student_name = student[0]


        safe_name = safe_face_name(student_name)


        # -------------------------------------------------
        # DELETE ATTENDANCE
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM attendance
            WHERE student_id = %s
        """, (student_id,))


        # -------------------------------------------------
        # DELETE STUDENT
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM students
            WHERE student_id = %s
        """, (student_id,))


        connection.commit()


        # -------------------------------------------------
        # DELETE FACE IMAGE
        # -------------------------------------------------

        image_path = os.path.join(
            "known_faces",
            safe_name + ".jpg"
        )


        if os.path.exists(image_path):

            try:

                os.remove(image_path)

                print(
                    f"Face image deleted: {image_path}"
                )

            except Exception as image_error:

                print(
                    "IMAGE DELETE ERROR:",
                    image_error
                )


        # -------------------------------------------------
        # REMOVE FROM MEMORY
        # -------------------------------------------------

        if safe_name in known_faces:

            del known_faces[safe_name]


        print(
            f"Student deleted successfully: "
            f"{student_name}"
        )


        return jsonify({

            "status": "success",

            "message":
                f"{student_name} deleted successfully"

        })


    except Exception as e:

        print(
            "DELETE STUDENT ERROR:",
            e
        )


        if connection:

            connection.rollback()


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
# ATTENDANCE API
# =========================================================

@app.route("/api/attendance")
def attendance_api():

    if not login_required():

        return jsonify({
            "status": "error",
            "message": "Login required"
        })


    connection = None
    cursor = None

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


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ATTENDANCE DASHBOARD
# =========================================================

@app.route("/attendance")
def attendance():

    if not login_required():

        return redirect("/login")


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()


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


        cursor.execute("""
            SELECT COUNT(*)
            FROM students
        """)


        total_students = cursor.fetchone()[0]


        cursor.execute("""
            SELECT COUNT(*)
            FROM attendance
            WHERE attendance_date = CURRENT_DATE
            AND status = 'Present'
        """)


        today_present = cursor.fetchone()[0]


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

<title>Attendance</title>

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

.actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 20px;
}

button {
    padding: 14px;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 16px;
}

.download {
    background: #d97706;
}

.home {
    background: #555;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 20px;
}

.stat {
    background: white;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
}

.number {
    font-size: 32px;
    font-weight: bold;
    color: #1f4e79;
}

.title {
    color: #666;
    margin-top: 8px;
}

.table-card {
    background: white;
    margin-top: 20px;
    border-radius: 15px;
    padding: 20px;
    overflow-x: auto;
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
    border-bottom: 1px solid #ddd;
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

@media(max-width:700px) {

    .stats {
        grid-template-columns: 1fr;
    }

    .actions {
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


<div class="actions">

<button
class="download"
onclick="location.href='/download-report'">

📥 Download CSV Report

</button>


<button
class="home"
onclick="location.href='/'">

⬅ Dashboard

</button>

</div>


<div class="stats">

<div class="stat">

<div class="number">
{{ total_students }}
</div>

<div class="title">
Total Students
</div>

</div>


<div class="stat">

<div class="number">
{{ today_present }}
</div>

<div class="title">
Present Today
</div>

</div>


<div class="stat">

<div class="number">
{{ today_absent }}
</div>

<div class="title">
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
        <h2>Attendance Error</h2>
        <p>{e}</p>
        """


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.route("/download-report")
def download_report():

    if not login_required():

        return redirect("/login")


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()


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


        output = StringIO()

        writer = csv.writer(output)


        writer.writerow([
            "Student Name",
            "Roll Number",
            "Date",
            "Time",
            "Status"
        ])


        for record in records:

            writer.writerow([
                record[0],
                record[1],
                record[2],
                record[3],
                record[4]
            ])


        response = Response(
            output.getvalue(),
            mimetype="text/csv"
        )


        response.headers[
            "Content-Disposition"
        ] = (
            "attachment; "
            "filename=attendance_report.csv"
        )


        return response


    except Exception as e:

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