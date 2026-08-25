import cv2
import psycopg2
from datetime import datetime
import numpy as np
import os
import base64

from flask import Flask, request, jsonify, render_template_string
from face_engine import detect_faces, known_faces


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "face_attendance"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "Postgres@123"),
        port=os.getenv("DB_PORT", "5432")
    )


# ============================================================
# DATABASE TEST
# ============================================================

try:

    connection = get_connection()
    connection.close()

    print("Database connected successfully!")

except Exception as e:

    print("Database connection failed:")
    print(e)


# ============================================================
# SAVE FACE ENCODINGS TO DATABASE
# ============================================================

def save_face_encodings():

    try:

        connection = get_connection()
        cursor = connection.cursor()

        for name, embedding in known_faces.items():

            encoding_text = ",".join(
                map(str, embedding.tolist())
            )

            cursor.execute(
                """
                UPDATE students
                SET face_encoding = %s
                WHERE LOWER(student_name) = LOWER(%s)
                """,
                (
                    encoding_text,
                    name
                )
            )

        connection.commit()

        cursor.close()
        connection.close()

        print("Face encodings saved to database!")

    except Exception as e:

        print("Face encoding database error:")
        print(e)


# Save encodings when application starts
save_face_encodings()


# ============================================================
# MARK ATTENDANCE
# ============================================================

def mark_attendance(student_name):

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Find student

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

            return {
                "success": False,
                "message": "Student not found in database."
            }

        student_id = student[0]

        today = datetime.now().date()
        current_time = datetime.now().time()

        # Check today's attendance

        cursor.execute(
            """
            SELECT attendance_id
            FROM attendance
            WHERE student_id = %s
            AND attendance_date = %s
            """,
            (
                student_id,
                today
            )
        )

        existing = cursor.fetchone()

        if existing:

            return {
                "success": False,
                "already_marked": True,
                "message": "Attendance already marked for today."
            }

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

        print(
            f"Attendance marked for {student_name}"
        )

        return {
            "success": True,
            "already_marked": False,
            "message": "Attendance marked successfully."
        }

    except Exception as e:

        if connection:
            connection.rollback()

        print("Attendance error:")
        print(e)

        return {
            "success": False,
            "message": "Database error."
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# FACE RECOGNITION
# ============================================================

def recognize_face(frame):

    try:

        faces = detect_faces(frame)

        if not faces:

            return {
                "status": "no_face",
                "message": "No face detected."
            }

        best_overall_name = "Unknown"
        best_overall_score = 0

        # Check all detected faces

        for face in faces:

            current_embedding = face.embedding

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

                if score > best_overall_score:

                    best_overall_score = score
                    best_overall_name = known_name

        # Recognition threshold

        if best_overall_score < 0.45:

            return {
                "status": "unknown",
                "message": "Unknown face.",
                "score": round(
                    float(best_overall_score),
                    4
                )
            }

        # Mark attendance

        attendance_result = mark_attendance(
            best_overall_name
        )

        return {
            "status": "recognized",
            "student": best_overall_name,
            "score": round(
                float(best_overall_score),
                4
            ),
            "attendance_marked":
                attendance_result.get(
                    "success",
                    False
                ),
            "already_marked":
                attendance_result.get(
                    "already_marked",
                    False
                ),
            "message":
                attendance_result.get(
                    "message",
                    "Recognition successful."
                )
        }

    except Exception as e:

        print("Recognition error:")
        print(e)

        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template_string(
        """
        <!DOCTYPE html>

        <html>

        <head>

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>AI Attendance System</title>

        <style>

        body {
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            text-align: center;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 500px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }

        h1 {
            margin-bottom: 20px;
        }

        button {
            width: 100%;
            padding: 14px;
            margin: 8px 0;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
        }

        .start {
            background: #2196f3;
            color: white;
        }

        .stop {
            background: #f44336;
            color: white;
        }

        video {
            width: 100%;
            border-radius: 12px;
            margin-top: 15px;
        }

        #result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            background: #eeeeee;
            font-size: 17px;
        }

        </style>

        </head>

        <body>

        <div class="container">

            <h1>AI Face Recognition Attendance</h1>

            <button class="start"
                    onclick="startCamera()">
                Start Camera
            </button>

            <button class="stop"
                    onclick="stopCamera()">
                Stop Camera
            </button>

            <video id="video"
                   autoplay
                   playsinline>
            </video>

            <canvas id="canvas"
                    style="display:none;">
            </canvas>

            <div id="result">
                Camera not started.
            </div>

        </div>


        <script>

        let video =
            document.getElementById("video");

        let canvas =
            document.getElementById("canvas");

        let result =
            document.getElementById("result");

        let stream = null;

        let recognitionInterval = null;


        async function startCamera() {

            try {

                stream =
                    await navigator.mediaDevices
                    .getUserMedia({
                        video: {
                            facingMode: "user"
                        },
                        audio: false
                    });

                video.srcObject = stream;

                result.innerHTML =
                    "Camera started. Looking for face...";

                recognitionInterval =
                    setInterval(
                        captureAndRecognize,
                        2000
                    );

            }

            catch(error) {

                console.log(error);

                result.innerHTML =
                    "Camera permission required. " +
                    "Please allow camera access.";
            }
        }


        function stopCamera() {

            if (recognitionInterval) {

                clearInterval(
                    recognitionInterval
                );

                recognitionInterval = null;
            }

            if (stream) {

                stream
                .getTracks()
                .forEach(
                    track => track.stop()
                );

                stream = null;
            }

            video.srcObject = null;

            result.innerHTML =
                "Camera stopped.";
        }


        async function captureAndRecognize() {

            if (!stream) {
                return;
            }

            if (video.videoWidth === 0) {
                return;
            }

            canvas.width =
                video.videoWidth;

            canvas.height =
                video.videoHeight;

            let context =
                canvas.getContext("2d");

            context.drawImage(
                video,
                0,
                0,
                canvas.width,
                canvas.height
            );

            let imageData =
                canvas.toDataURL(
                    "image/jpeg",
                    0.8
                );

            try {

                let response =
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

                let data =
                    await response.json();


                if (data.status === "recognized") {

                    if (data.attendance_marked) {

                        result.innerHTML =
                            "✅ <b>" +
                            data.student +
                            "</b><br>" +
                            "Attendance Marked<br>" +
                            "Score: " +
                            data.score;

                    }

                    else if (data.already_marked) {

                        result.innerHTML =
                            "ℹ️ <b>" +
                            data.student +
                            "</b><br>" +
                            "Attendance Already Marked<br>" +
                            "Score: " +
                            data.score;

                    }

                    else {

                        result.innerHTML =
                            "✅ <b>" +
                            data.student +
                            "</b><br>" +
                            data.message;
                    }

                }

                else if (
                    data.status === "unknown"
                ) {

                    result.innerHTML =
                        "❌ Unknown Face";

                }

                else if (
                    data.status === "no_face"
                ) {

                    result.innerHTML =
                        "👤 No Face Detected";

                }

                else {

                    result.innerHTML =
                        "⚠️ " +
                        data.message;
                }

            }

            catch(error) {

                console.log(error);

                result.innerHTML =
                    "Server connection error.";
            }
        }

        </script>

        </body>

        </html>
        """
    )


# ============================================================
# RECOGNIZE API
# ============================================================

@app.route(
    "/recognize",
    methods=["POST"]
)
def recognize():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "status": "error",
                "message": "No data received."
            }), 400

        image_data = data.get("image")

        if not image_data:

            return jsonify({
                "status": "error",
                "message": "No image received."
            }), 400

        # Remove base64 header

        if "," in image_data:

            image_data = image_data.split(
                ",",
                1
            )[1]

        # Decode image

        image_bytes = base64.b64decode(
            image_data
        )

        # Convert to numpy

        np_array = np.frombuffer(
            image_bytes,
            np.uint8
        )

        # Convert to OpenCV image

        frame = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:

            return jsonify({
                "status": "error",
                "message": "Invalid image."
            }), 400

        # Recognize

        result = recognize_face(frame)

        return jsonify(result)

    except Exception as e:

        print("API error:")
        print(e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "message": "AI Attendance System is running."
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )