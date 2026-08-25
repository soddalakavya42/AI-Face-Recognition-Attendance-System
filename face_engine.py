import cv2
import os
import numpy as np
from insightface.app import FaceAnalysis


# =========================================================
# FACE RECOGNITION MODEL
# =========================================================

face_app = FaceAnalysis(
    name="buffalo_s",
    providers=["CPUExecutionProvider"]
)

face_app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)


# =========================================================
# KNOWN FACES
# =========================================================

known_faces = {}

known_faces_folder = "known_faces"


# =========================================================
# LOAD KNOWN FACES
# =========================================================

def load_known_faces():

    global known_faces

    known_faces = {}

    if not os.path.exists(known_faces_folder):
        print("known_faces folder not found")
        return known_faces

    for filename in os.listdir(known_faces_folder):

        if not filename.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):
            continue

        image_path = os.path.join(
            known_faces_folder,
            filename
        )

        image = cv2.imread(image_path)

        if image is None:
            print(f"Could not read: {filename}")
            continue

        faces = face_app.get(image)

        if len(faces) == 0:
            print(f"No face found: {filename}")
            continue

        name = os.path.splitext(filename)[0]

        known_faces[name] = faces[0].embedding

        print(f"Loaded known face: {name}")

    return known_faces


# =========================================================
# LOAD FACES AT START
# =========================================================

load_known_faces()


# =========================================================
# REGISTER NEW FACE
# =========================================================

def register_face(image, name):

    if image is None:
        return False, "Invalid image"

    if not name:
        return False, "Name is required"

    faces = face_app.get(image)

    if len(faces) == 0:
        return False, "No face detected"

    if len(faces) > 1:
        return False, "Multiple faces detected. Please use one face."

    os.makedirs(known_faces_folder, exist_ok=True)

    filename = f"{name}.jpg"

    image_path = os.path.join(
        known_faces_folder,
        filename
    )

    success = cv2.imwrite(
        image_path,
        image
    )

    if not success:
        return False, "Failed to save image"

    embedding = faces[0].embedding

    known_faces[name] = embedding

    print(f"Registered new face: {name}")

    return True, "Face registered successfully"


# =========================================================
# DETECT FACES
# =========================================================

def detect_faces(frame):

    if frame is None:
        return []

    faces = face_app.get(frame)

    return faces


# =========================================================
# RECOGNIZE SINGLE FACE
# =========================================================

def recognize_face(face):

    if not known_faces:
        return "Unknown", 0.0

    current_embedding = face.embedding

    best_name = "Unknown"
    best_score = 0.0

    for known_name, known_embedding in known_faces.items():

        denominator = (
            np.linalg.norm(current_embedding)
            * np.linalg.norm(known_embedding)
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

    if best_score > 0.50:
        return best_name, best_score

    return "Unknown", best_score


# =========================================================
# DRAW & RECOGNIZE FACES
# =========================================================

def draw_faces(frame, faces):

    for face in faces:

        x1, y1, x2, y2 = face.bbox.astype(int)

        name, score = recognize_face(face)

        label = name

        if name != "Unknown":
            label = f"{name} ({score:.2f})"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    return frame