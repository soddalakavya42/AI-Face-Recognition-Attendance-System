import cv2
import os
import numpy as np
from insightface.app import FaceAnalysis

face_app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

face_app.prepare(ctx_id=0, det_size=(640, 640))


# Load known face
known_faces = {}

known_faces_folder = "known_faces"

for filename in os.listdir(known_faces_folder):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):

        image_path = os.path.join(known_faces_folder, filename)
        image = cv2.imread(image_path)

        faces = face_app.get(image)

        if len(faces) > 0:
            name = os.path.splitext(filename)[0]
            known_faces[name] = faces[0].embedding

            print(f"Loaded known face: {name}")


def detect_faces(frame):
    faces = face_app.get(frame)
    return faces


def draw_faces(frame, faces):

    for face in faces:

        x1, y1, x2, y2 = face.bbox.astype(int)

        name = "Unknown"

        if known_faces:
            current_embedding = face.embedding

            best_name = "Unknown"
            best_score = 0

            for known_name, known_embedding in known_faces.items():

                score = np.dot(current_embedding, known_embedding) / (
                    np.linalg.norm(current_embedding)
                    * np.linalg.norm(known_embedding)
                )

                if score > best_score:
                    best_score = score
                    best_name = known_name

            if best_score > 0.50:
                name = best_name

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            name,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    return frame