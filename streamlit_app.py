import streamlit as st
import cv2
import numpy as np
from PIL import Image

from face_engine import (
    face_app,
    known_faces,
    load_known_faces,
    register_face,
    detect_faces
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Face Recognition Attendance System",
    page_icon="🎓",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🎓 AI Face Recognition Attendance System")
st.caption("AI-powered Face Recognition Attendance System")


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📌 Menu")

menu = st.sidebar.radio(
    "Select Option",
    [
        "🏠 Dashboard",
        "📷 Face Recognition",
        "👤 Register Student",
        "👥 Known Faces"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.header("🏠 Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Registered Faces",
            len(known_faces)
        )

    with col2:
        st.metric(
            "AI Model",
            "InsightFace"
        )

    with col3:
        st.metric(
            "Recognition",
            "Cosine Similarity"
        )

    st.success(
        "✅ AI Face Recognition Attendance System is running!"
    )

    st.info(
        "Use the sidebar to register students or recognize faces."
    )


# =========================================================
# FACE RECOGNITION
# =========================================================

elif menu == "📷 Face Recognition":

    st.header("📷 Face Recognition")

    st.write(
        "Capture an image using your camera and recognize the face."
    )

    camera_image = st.camera_input(
        "Take a picture"
    )

    if camera_image is not None:

        image = Image.open(
            camera_image
        )

        frame = np.array(
            image
        )

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2BGR
        )

        with st.spinner(
            "🔍 Recognizing face..."
        ):

            faces = detect_faces(
                frame
            )

        if len(faces) == 0:

            st.error(
                "❌ No face detected."
            )

        else:

            face = max(
                faces,
                key=lambda x: (
                    x.bbox[2] - x.bbox[0]
                ) * (
                    x.bbox[3] - x.bbox[1]
                )
            )

            current_embedding = (
                face.embedding
            )

            best_name = "Unknown"
            best_score = 0.0

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

                st.success(
                    f"✅ Recognized: {best_name}"
                )

                st.metric(
                    "Similarity Score",
                    f"{best_score:.2f}"
                )

                st.info(
                    "Face recognized successfully."
                )

            else:

                st.warning(
                    "⚠️ Unknown Face"
                )

                st.metric(
                    "Similarity Score",
                    f"{best_score:.2f}"
                )


# =========================================================
# REGISTER STUDENT
# =========================================================

elif menu == "👤 Register Student":

    st.header("👤 Register New Student")

    name = st.text_input(
        "Student Name"
    )

    captured_image = st.camera_input(
        "Capture Student Face"
    )

    if st.button(
        "➕ Register Student"
    ):

        if not name.strip():

            st.error(
                "Please enter student name."
            )

        elif captured_image is None:

            st.error(
                "Please capture a face image."
            )

        else:

            image = Image.open(
                captured_image
            )

            frame = np.array(
                image
            )

            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2BGR
            )

            with st.spinner(
                "Registering face..."
            ):

                success, message = register_face(
                    name,
                    frame
                )

            if success:

                st.success(
                    f"✅ Student '{message}' registered successfully!"
                )

            else:

                st.error(
                    f"❌ {message}"
                )


# =========================================================
# KNOWN FACES
# =========================================================

elif menu == "👥 Known Faces":

    st.header("👥 Registered Students")

    load_known_faces()

    if len(known_faces) == 0:

        st.warning(
            "No registered faces found."
        )

    else:

        st.success(
            f"Total registered faces: {len(known_faces)}"
        )

        for name in known_faces:

            st.write(
                f"👤 {name}"
            )