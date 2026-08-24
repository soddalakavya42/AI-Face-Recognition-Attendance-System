import cv2
import os
import numpy as np
from insightface.app import FaceAnalysis


# =========================================================
# FACE AI MODEL
# =========================================================

face_app = FaceAnalysis(
    name="buffalo_l",
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


# Create folder if it does not exist
os.makedirs(
    known_faces_folder,
    exist_ok=True
)


# =========================================================
# LOAD KNOWN FACES
# =========================================================

def load_known_faces():

    global known_faces

    known_faces = {}

    for filename in os.listdir(
        known_faces_folder
    ):

        if filename.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):

            image_path = os.path.join(
                known_faces_folder,
                filename
            )

            image = cv2.imread(
                image_path
            )

            if image is None:
                continue

            faces = face_app.get(
                image
            )

            if len(faces) > 0:

                name = os.path.splitext(
                    filename
                )[0]

                known_faces[name] = (
                    faces[0].embedding
                )

                print(
                    f"Loaded known face: {name}"
                )


# Load faces when application starts
load_known_faces()


# =========================================================
# DETECT FACES
# =========================================================

def detect_faces(frame):

    faces = face_app.get(
        frame
    )

    return faces


# =========================================================
# REGISTER NEW FACE
# =========================================================

def register_face(
    name,
    image
):

    if image is None:

        return False, "Invalid image"


    faces = face_app.get(
        image
    )


    if len(faces) == 0:

        return False, "Face not detected"


    if len(faces) > 1:

        return False, "Multiple faces detected"


    face = faces[0]


    embedding = face.embedding


    filename = (
        name.strip()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        + ".jpg"
    )


    image_path = os.path.join(
        known_faces_folder,
        filename
    )


    saved = cv2.imwrite(
        image_path,
        image
    )


    if not saved:

        return False, "Face image could not be saved"


    # Add immediately to memory
    clean_name = os.path.splitext(
        filename
    )[0]


    known_faces[clean_name] = (
        embedding
    )


    print(
        f"Registered new face: {clean_name}"
    )


    return True, clean_name


# =========================================================
# DRAW FACE RECOGNITION
# =========================================================

def draw_faces(
    frame,
    faces
):

    for face in faces:

        x1, y1, x2, y2 = (
            face.bbox.astype(int)
        )


        name = "Unknown"


        if known_faces:

            current_embedding = (
                face.embedding
            )

            best_name = "Unknown"
            best_score = 0


            for (
                known_name,
                known_embedding
            ) in known_faces.items():

                score = np.dot(
                    current_embedding,
                    known_embedding
                ) / (
                    np.linalg.norm(
                        current_embedding
                    )
                    *
                    np.linalg.norm(
                        known_embedding
                    )
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