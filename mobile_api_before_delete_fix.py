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


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "smart-attendance-secret-key"


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
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == "admin"
            and password == "admin123"
        ):

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

.login-container {

    max-width: 400px;

    margin: 80px auto;

    padding: 20px;
}

.card {

    background: white;

    padding: 30px;

    border-radius: 18px;

    box-shadow:
        0 4px 15px
        rgba(0,0,0,0.10);
}

h1 {

    text-align: center;

    color: #1f4e79;
}

.subtitle {

    text-align: center;

    color: #666;

    margin-bottom: 25px;
}

input {

    width: 100%;

    padding: 14px;

    margin-top: 10px;

    margin-bottom: 15px;

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

    cursor: pointer;
}

.error {

    background: #f8d7da;

    color: #842029;

    padding: 12px;

    border-radius: 8px;

    margin-bottom: 15px;

    text-align: center;
}

</style>

</head>


<body>


<div class="login-container">

<div class="card">

<h1>
🔐 Smart Attendance
</h1>

<p class="subtitle">
Admin Login
</p>

<div class="error">
Invalid username or password
</div>

<form method="POST">

<input
type="text"
name="username"
placeholder="Username"
required
>

<input
type="password"
name="password"
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

.login-container {

    max-width: 400px;

    margin: 80px auto;

    padding: 20px;
}

.card {

    background: white;

    padding: 30px;

    border-radius: 18px;

    box-shadow:
        0 4px 15px
        rgba(0,0,0,0.10);
}

h1 {

    text-align: center;

    color: #1f4e79;
}

.subtitle {

    text-align: center;

    color: #666;

    margin-bottom: 25px;
}

input {

    width: 100%;

    padding: 14px;

    margin-top: 10px;

    margin-bottom: 15px;

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

    cursor: pointer;
}

</style>

</head>


<body>


<div class="login-container">

<div class="card">

<h1>
🔐 Smart Attendance
</h1>

<p class="subtitle">
Admin Login
</p>

<form method="POST">

<input
type="text"
name="username"
placeholder="Username"
required
>

<input
type="password"
name="password"
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

@app.before_request
def require_login():

    public_routes = [
        "login",
        "static"
    ]

    if request.endpoint in public_routes:
        return

    if not session.get("logged_in"):
        return redirect("/login")


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def home():

    return render_template_string("""
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

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

    position: relative;
}

.header h1 {

    margin: 0;

    font-size: 28px;
}

.header p {

    margin-bottom: 0;

    opacity: 0.9;
}

.logout {

    position: absolute;

    right: 20px;

    top: 20px;

    background: #b52b27;

    color: white;

    text-decoration: none;

    padding: 9px 14px;

    border-radius: 8px;
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

    box-shadow:
        0 3px 12px
        rgba(0,0,0,0.08);
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

.camera {

    background: #198754;
}

.students {

    background: #6f42c1;
}

.report {

    background: #d97706;
}

.add {

    background: #0d9488;
}

</style>

</head>


<body>


<div class="header">

<a href="/logout" class="logout">
Logout
</a>

<h1>
Smart Attendance System
</h1>

<p>
AI Face Recognition Based Attendance
</p>

</div>


<div class="container">


<!-- ATTENDANCE -->

<div class="card">

<h2>
📷 Face Attendance
</h2>

<p class="info">

Daily attendance kosam
face recognition use cheyyandi.

</p>

<button
class="button camera"
onclick="location.href='/attendance-page'">

▶ Start Attendance

</button>

</div>


<!-- STUDENT MANAGEMENT -->

<div class="card">

<h2>
👥 Student Management
</h2>

<p class="info">

Kotha student vachinappudu matrame
ikkada nundi add cheyyandi.

</p>

<button
class="button add"
onclick="location.href='/add-student'">

➕ Add Student

</button>


<button
class="button students"
onclick="location.href='/students'">

👥 View Students

</button>

</div>


<!-- ATTENDANCE -->

<div class="card">

<h2>
📊 Attendance Dashboard
</h2>

<p class="info">

Attendance records,
present and absent students chudandi.

</p>

<button
class="button"
onclick="location.href='/attendance'">

📊 View Attendance

</button>

</div>


<!-- REPORT -->

<div class="card">

<h2>
📥 Attendance Report
</h2>

<p class="info">

Attendance records ni CSV file ga download cheyyandi.

</p>

<button
class="button report"
onclick="location.href='/download-report'">

📥 Download CSV Report

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

    cursor: pointer;
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

    padding: 18px;

    border-radius: 10px;

    background: white;

    font-size: 20px;

    font-weight: bold;

    line-height: 1.7;
}

.recognized {

    color: #198754;
}

.marked {

    color: #1f4e79;
}

.unknown {

    color: #b52b27;
}

</style>

</head>


<body>


<div class="container">


<h1>
📷 Face Attendance
</h1>


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

⬅ Back to Dashboard

</button>


<div id="result">

Waiting for camera...

</div>


</div>


<script>

let stream = null;

let timer = null;

let processing = false;

let attendanceMarked = false;


async function startCamera() {

    try {

        if (stream) {
            return;
        }

        attendanceMarked = false;

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
            "📷 Camera started.<br>" +
            "Face ni camera mundu pettandi...";


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

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Camera permission required.";

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


    document.getElementById(
        "camera"
    ).srcObject = null;


    document.getElementById(
        "result"
    ).innerHTML =
        "📷 Camera stopped.";

}


async function captureFrame() {

    if (
        processing ||
        attendanceMarked
    ) {

        return;

    }


    const video =
        document.getElementById(
            "camera"
        );


    if (
        video.readyState !==
        video.HAVE_ENOUGH_DATA
    ) {

        return;

    }


    processing = true;


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


        if (
            data.status ===
            "success"
        ) {

            if (
                data.already_marked ===
                true
            ) {

                document.getElementById(
                    "result"
                ).innerHTML =

                    "<span class='recognized'>" +
                    "✅ Recognized: " +
                    data.student +
                    "</span><br>" +

                    "<span class='marked'>" +
                    "📋 Attendance Already Marked Today" +
                    "</span>";

            }

            else {

                document.getElementById(
                    "result"
                ).innerHTML =

                    "<span class='recognized'>" +
                    "✅ Recognized: " +
                    data.student +
                    "</span><br>" +

                    "<span class='marked'>" +
                    "📋 Attendance Marked Successfully" +
                    "</span>";

            }


            attendanceMarked = true;


            if (timer) {

                clearInterval(timer);

                timer = null;

            }

        }


        else if (
            data.status ===
            "unknown"
        ) {

            document.getElementById(
                "result"
            ).innerHTML =

                "<span class='unknown'>" +
                "❌ Unknown Face" +
                "</span><br>" +

                "Please register this student.";

        }


        else if (
            data.status ===
            "no_face"
        ) {

            document.getElementById(
                "result"
            ).innerHTML =

                "👤 <b>Face Not Detected</b><br>" +

                "Please look at the camera.";

        }


        else {

            document.getElementById(
                "result"
            ).innerHTML =

                "⚠️ " +
                data.message;

        }

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Server error.";

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

@app.route(
    "/recognize",
    methods=["POST"]
)
def recognize():

    connection = None

    cursor = None

    try:

        data = request.get_json()


        if (
            not data
            or "image" not in data
        ):

            return jsonify({

                "status": "error",

                "message":
                    "Image not received"

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

                "message":
                    "Invalid image"

            })


        faces = detect_faces(
            frame
        )


        if len(faces) == 0:

            return jsonify({

                "status": "no_face",

                "message":
                    "Face not detected"

            })


        face = max(
            faces,
            key=lambda f:
                (f.bbox[2] - f.bbox[0])
                *
                (f.bbox[3] - f.bbox[1])
        )


        current_embedding = (
            face.embedding
        )


        best_name = "Unknown"

        best_score = 0


        for (
            known_name,
            known_embedding
        ) in known_faces.items():

            denominator = (
                np.linalg.norm(
                    current_embedding
                )
                *
                np.linalg.norm(
                    known_embedding
                )
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

                "message":
                    "Unknown face",

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


        if already_marked is not None:

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
            f"Attendance marked for {student_name}"
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

    box-shadow:
        0 3px 12px
        rgba(0,0,0,0.08);
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

    background: #1f4e79;

    font-size: 17px;

    cursor: pointer;
}

.capture {

    background: #198754;
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


<h1>
➕ Add Student
</h1>


<label>
Student Name
</label>

<input
id="studentName"
type="text"
placeholder="Enter student name"
required
>


<label>
Roll Number
</label>

<input
id="rollNumber"
type="text"
placeholder="Enter roll number"
required
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

⬅ Back to Dashboard

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
            "📷 Camera started. " +
            "Face ni camera mundu pettandi.";

    }

    catch(error) {

        console.log(error);

        document.getElementById(
            "result"
        ).innerHTML =
            "❌ Camera permission required.";

        alert(
            "Camera permission allow cheyyandi."
        );

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
        video.videoWidth === 0
        ||
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
        "✅ Face photo captured. " +
        "Save Student click cheyyandi.";

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
            data.status ===
            "success"
        ) {

            document.getElementById(
                "result"
            ).innerHTML =
                "✅ " +
                data.message;


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
                1500
            );

        }

        else {

            document.getElementById(
                "result"
            ).innerHTML =
                "❌ " +
                data.message;

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

@app.route(
    "/api/students/add",
    methods=["POST"]
)
def add_student():

    connection = None

    cursor = None

    try:

        data = request.get_json()


        if not data:

            return jsonify({

                "status": "error",

                "message":
                    "Data not received"

            })


        student_name = (
            data.get(
                "student_name",
                ""
            ).strip()
        )


        roll_number = (
            data.get(
                "roll_number",
                ""
            ).strip()
        )


        email = (
            data.get(
                "email",
                ""
            ).strip()
        )


        image_data = data.get(
            "image",
            ""
        )


        if not student_name:

            return jsonify({

                "status": "error",

                "message":
                    "Student name required"

            })


        if not roll_number:

            return jsonify({

                "status": "error",

                "message":
                    "Roll number required"

            })


        if not image_data:

            return jsonify({

                "status": "error",

                "message":
                    "Face image required"

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

            WHERE LOWER(student_name)
                = LOWER(%s)

            OR LOWER(roll_number)
                = LOWER(%s)

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


        try:

            image_bytes = base64.b64decode(
                image_data
            )

        except Exception:

            return jsonify({

                "status": "error",

                "message":
                    "Invalid image data"

            })


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

                "message":
                    "Invalid image"

            })


        success, result = register_face(
            student_name,
            frame
        )


        if not success:

            return jsonify({

                "status": "error",

                "message":
                    result

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
                student_id,

            "student":
                student_name

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
    methods=["POST"]
)
def delete_student(student_id):

    connection = None

    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()


        # -------------------------------------------------
        # Find student
        # -------------------------------------------------

        cursor.execute("""

            SELECT
                student_name

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


        # -------------------------------------------------
        # Delete attendance first
        # -------------------------------------------------

        cursor.execute("""

            DELETE FROM attendance

            WHERE student_id = %s

        """, (student_id,))


        # -------------------------------------------------
        # Delete student
        # -------------------------------------------------

        cursor.execute("""

            DELETE FROM students

            WHERE student_id = %s

        """, (student_id,))


        connection.commit()


        # -------------------------------------------------
        # Build face filename
        # Same logic used by register_face()
        # -------------------------------------------------

        clean_name = (

            student_name
            .strip()
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")

        )


        # -------------------------------------------------
        # Remove from memory
        # -------------------------------------------------

        if clean_name in known_faces:

            del known_faces[clean_name]


        # -------------------------------------------------
        # Remove face image
        # -------------------------------------------------

        face_file = os.path.join(
            "known_faces",
            clean_name + ".jpg"
        )


        if os.path.exists(face_file):

            os.remove(face_file)

            print(
                f"Face image deleted: {face_file}"
            )


        print(
            f"Student deleted: {student_name}"
        )


        return jsonify({

            "status": "success",

            "message":
                f"Student {student_name} deleted successfully"

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
# STUDENTS PAGE
# =========================================================

@app.route("/students")
def students():

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

    margin-bottom: 20px;
}

.add-button {

    width: 100%;

    padding: 15px;

    margin-bottom: 18px;

    border: none;

    border-radius: 10px;

    background: #0d9488;

    color: white;

    font-size: 17px;

    cursor: pointer;
}

.card {

    background: white;

    padding: 18px;

    margin-bottom: 14px;

    border-radius: 12px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,0.08);
}

.name {

    font-size: 20px;

    font-weight: bold;

    color: #1f4e79;

    margin-bottom: 10px;
}

.info {

    color: #555;

    margin-top: 6px;
}

.delete-button {

    width: 100%;

    padding: 13px;

    margin-top: 15px;

    border: none;

    border-radius: 9px;

    background: #dc3545;

    color: white;

    font-size: 16px;

    cursor: pointer;
}

.back-button {

    width: 100%;

    padding: 14px;

    margin-top: 10px;

    border: none;

    border-radius: 10px;

    background: #555;

    color: white;

    font-size: 17px;

    cursor: pointer;
}

.empty {

    background: white;

    padding: 25px;

    text-align: center;

    border-radius: 12px;

    color: #777;
}

</style>

</head>


<body>


<div class="container">


<h1>
👥 Registered Students
</h1>


<button
class="add-button"
onclick="location.href='/add-student'">

➕ Add Student Using Camera

</button>


{% for student in records %}


<div class="card">


<div class="name">

{{ student[1] }}

</div>


<div class="info">

Student ID:
{{ student[0] }}

</div>


<div class="info">

Roll Number:
{{ student[2] }}

</div>


<div class="info">

Email:
{{ student[3] if student[3] else 'Not provided' }}

</div>


<button
class="delete-button"
onclick="deleteStudent(
    {{ student[0] }},
    {{ student[1]|tojson }}
)">

🗑️ Delete Student

</button>


</div>


{% endfor %}


{% if not records %}

<div class="empty">

No students found.

</div>

{% endif %}


<button
class="back-button"
onclick="location.href='/'">

⬅ Back to Dashboard

</button>


</div>


<script>


async function deleteStudent(
    studentId,
    studentName
) {


    const confirmed = confirm(

        "Are you sure you want to delete " +
        studentName +
        "?\\n\\n" +

        "Student database record, " +
        "attendance records and face data " +
        "will be deleted."

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

                    method: "POST"

                }

            );


        const data =
            await response.json();


        if (
            data.status ===
            "success"
        ) {


            alert(
                "✅ " +
                data.message
            );


            location.reload();


        }

        else {


            alert(
                "❌ " +
                data.message
            );


        }


    }

    catch(error) {


        console.log(error);


        alert(
            "❌ Server error. " +
            "Please try again."
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
# ATTENDANCE API
# =========================================================

@app.route("/api/attendance")
def attendance_api():

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


        total_students = (
            cursor.fetchone()[0]
        )


        cursor.execute("""

            SELECT COUNT(*)

            FROM attendance

            WHERE attendance_date = CURRENT_DATE

            AND status = 'Present'

        """)


        today_present = (
            cursor.fetchone()[0]
        )


        today_absent = (
            total_students
            -
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

.actions {

    display: grid;

    grid-template-columns: 1fr 1fr;

    gap: 12px;

    margin-top: 20px;
}

.action-button {

    padding: 14px;

    border: none;

    border-radius: 10px;

    color: white;

    font-size: 16px;

    cursor: pointer;
}

.download {

    background: #d97706;
}

.home {

    background: #555;
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

.present {

    color: #198754;

    font-weight: bold;
}

.empty {

    text-align: center;

    padding: 30px;

    color: #777;
}

@media(max-width: 700px) {

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

<h1>
📊 Attendance Dashboard
</h1>

<p>
Smart Attendance System
</p>

</div>


<div class="actions">


<button
class="action-button download"
onclick="location.href='/download-report'">

📥 Download CSV Report

</button>


<button
class="action-button home"
onclick="location.href='/'">

⬅ Back to Dashboard

</button>


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


<h2>
Attendance Records
</h2>


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
        <h2>Attendance Dashboard Error</h2>
        <p>{e}</p>
        """


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# DOWNLOAD ATTENDANCE REPORT
# =========================================================

@app.route("/download-report")
def download_report():

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


        writer = csv.writer(
            output
        )


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