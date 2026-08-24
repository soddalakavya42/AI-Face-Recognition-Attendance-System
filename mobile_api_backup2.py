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

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Smart Attendance System</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #f2f4f7;
    margin: 0;
}

.header {
    background: #1f4e79;
    color: white;
    padding: 25px 15px;
    text-align: center;
}

.header h1 {
    margin: 0;
    font-size: 26px;
}

.container {
    padding: 20px;
}

.card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
}

.card h2 {
    margin-top: 0;
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
}

.button:active {
    background: #163a5c;
}

.info {
    color: #555;
}

</style>

</head>

<body>

<div class="header">

<h1>Smart Attendance System</h1>

<p>AI Face Recognition</p>

</div>

<div class="container">

<div class="card">

<h2>📷 Start Attendance</h2>

<p class="info">
Use AI face recognition to mark attendance.
</p>

<button
class="button"
onclick="location.href='/attendance-page'">

Start Attendance

</button>

</div>


<div class="card">

<h2>📊 View Attendance</h2>

<p class="info">
View attendance records.
</p>

<button
class="button"
onclick="location.href='/attendance'">

View Attendance

</button>

</div>


<div class="card">

<h2>👥 View Students</h2>

<p class="info">
View registered students.
</p>

<button
class="button"
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

body {
    font-family: Arial;
    text-align: center;
    background: #f2f4f7;
    padding: 15px;
}

video {
    width: 100%;
    max-width: 500px;
    border-radius: 15px;
    background: black;
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

#result {
    margin-top: 20px;
    padding: 15px;
    border-radius: 10px;
    background: white;
    font-size: 18px;
    font-weight: bold;
}

</style>

</head>


<body>

<h1>📷 Face Attendance</h1>

<p>Camera start chesi face ni camera mundu pettandi.</p>


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


<div id="result">
Waiting for camera...
</div>


<script>

let stream = null;
let timer = null;
let processing = false;


async function startCamera() {

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "user"
            },
            audio: false
        });

        document.getElementById("camera").srcObject = stream;

        document.getElementById("result").innerText =
            "Camera started. Face ni camera mundu pettandi...";

        timer = setInterval(captureFrame, 1500);

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

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;


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
            await fetch("/recognize", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    image: imageData
                })

            });


        const data =
            await response.json();


        if (data.status === "success") {

            document.getElementById(
                "result"
            ).innerText =
                "✅ " +
                data.message;

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
                "⚠️ " +
                data.message;

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

    try:

        data = request.get_json()

        if not data or "image" not in data:

            return jsonify({
                "status": "error",
                "message": "Image not received"
            })


        image_data = data["image"]


        # Remove base64 header
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]


        image_bytes = base64.b64decode(image_data)


        # Convert bytes to OpenCV image
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


        # Detect faces
        faces = detect_faces(frame)


        if len(faces) == 0:

            return jsonify({
                "status": "no_face",
                "message": "Face not detected"
            })


        # Take largest face
        face = max(
            faces,
            key=lambda f:
            (f.bbox[2] - f.bbox[0]) *
            (f.bbox[3] - f.bbox[1])
        )


        current_embedding = face.embedding


        best_name = "Unknown"
        best_score = 0


        # Compare with known faces
        for known_name, known_embedding in known_faces.items():

            score = np.dot(
                current_embedding,
                known_embedding
            ) / (
                np.linalg.norm(current_embedding) *
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


        # Recognition threshold
        if best_score < 0.50:

            return jsonify({
                "status": "unknown",
                "message": "Unknown face",
                "score": round(float(best_score), 3)
            })


        # =================================================
        # FIND STUDENT IN DATABASE
        # =================================================

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

            cursor.close()
            connection.close()

            return jsonify({
                "status": "error",
                "message":
                    f"{best_name} database lo student ga ledu"
            })


        student_id = student[0]
        student_name = student[1]


        # =================================================
        # CHECK TODAY ATTENDANCE
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


        if already_marked is not None:

            cursor.close()
            connection.close()

            return jsonify({
                "status": "success",
                "message":
                    f"{student_name} attendance already marked today",
                "student": student_name,
                "score": round(float(best_score), 3)
            })


        # =================================================
        # INSERT ATTENDANCE
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


        cursor.close()
        connection.close()


        return jsonify({
            "status": "success",
            "message":
                f"Attendance marked for {student_name}",
            "student": student_name,
            "score": round(float(best_score), 3)
        })


    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })


# =========================================================
# STUDENTS
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


        students_list = []


        for record in records:

            students_list.append({

                "student_id": record[0],

                "student_name": record[1],

                "roll_number": record[2],

                "email": record[3]

            })


        return jsonify(students_list)


    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })


# =========================================================
# ATTENDANCE
# =========================================================

@app.route("/attendance")
def attendance():

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

                "student_name": record[0],

                "date": str(record[1]),

                "time": str(record[2]),

                "status": record[3]

            })


        return jsonify(attendance_list)


    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })


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