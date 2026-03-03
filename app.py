import streamlit as st
import pickle
import numpy as np
from datetime import datetime
import random
import sqlite3
import qrcode
import time
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

st.set_page_config(page_title="PreventAI Clinical System", layout="wide")

# ---------------- DATABASE ---------------- #
conn = sqlite3.connect("preventai.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    patient_id TEXT,
    verification_id TEXT,
    probability REAL,
    category TEXT,
    doctor TEXT,
    timestamp TEXT
)
""")
conn.commit()

# ---------------- LOAD MODEL ---------------- #
model = pickle.load(open("model.pkl", "rb"))

# ---------------- LOGIN ---------------- #
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:

    st.title("🔐 PreventAI Secure Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == "admin" and password == "1234":
            st.session_state.role = "Admin"
            st.success("Logged in as Admin")

        elif username == "doctor" and password == "5678":
            st.session_state.role = "Doctor"
            st.success("Logged in as Doctor")

        else:
            st.error("Invalid Credentials")

else:

    st.sidebar.success(f"Logged in as {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    # ---------------- HEADER ---------------- #
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("hospital_logo.png", width=120)
    with col2:
        st.title("PreventAI Clinical Intelligence System")
        st.caption("AI Powered Certified Medical Risk Evaluation Platform")

    st.markdown("---")

    patient_id = f"PA-{random.randint(10000,99999)}"
    verification_id = f"VER-{random.randint(100000,999999)}"

    # ---------------- INPUT ---------------- #
    preg = st.number_input("Pregnancies", min_value=0)
    glucose = st.number_input("Glucose Level (mg/dL)", min_value=0)
    bp = st.number_input("Blood Pressure (mm Hg)", min_value=0)
    skin = st.number_input("Skin Thickness (mm)", min_value=0)
    insulin = st.number_input("Insulin Level (mu U/ml)", min_value=0)
    bmi = st.number_input("BMI", min_value=0.0)
    dpf = st.number_input("Diabetes Pedigree Function", min_value=0.0)
    age = st.number_input("Age", min_value=0)

    if st.button("Generate Clinical Report"):

        with st.spinner("AI Processing..."):
            time.sleep(2)

        input_data = np.array([[preg, glucose, bp, skin, insulin, bmi, dpf, age]])
        probability = model.predict_proba(input_data)[0][1] * 100

        if probability < 30:
            category = "LOW"
            doctor = "Dr. Priya Menon"
        elif probability < 70:
            category = "MODERATE"
            doctor = "Dr. Ramesh Iyer"
        else:
            category = "HIGH"
            doctor = "Dr. R. Kumar"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?)",
            (patient_id, verification_id, probability, category, doctor, timestamp)
        )
        conn.commit()

        st.subheader("📋 Clinical Report Summary")
        st.write(f"Patient ID: {patient_id}")
        st.write(f"Verification ID: {verification_id}")
        st.write(f"Risk Probability: {probability:.2f}%")
        st.write(f"Risk Category: {category}")
        st.write(f"Assigned Doctor: {doctor}")
        st.write(f"Generated On: {timestamp}")

        # -------- QR -------- #
        qr_data = f"{patient_id} | {verification_id} | {category}"
        qr = qrcode.make(qr_data)
        qr_filename = f"{patient_id}_QR.png"
        qr.save(qr_filename)

        st.image(qr_filename, width=150)

        # -------- PDF -------- #
        pdf_filename = f"{patient_id}_Certified_Report.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        elements = []
        style = ParagraphStyle(name='Normal', fontSize=11)

        elements.append(Image("hospital_logo.png", width=2*inch, height=1*inch))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("PreventAI Certified Clinical Report", style))
        elements.append(Paragraph(f"Patient ID: {patient_id}", style))
        elements.append(Paragraph(f"Verification ID: {verification_id}", style))
        elements.append(Paragraph(f"Risk Probability: {probability:.2f}%", style))
        elements.append(Paragraph(f"Risk Category: {category}", style))
        elements.append(Paragraph(f"Assigned Doctor: {doctor}", style))
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Digital Signature:", style))
        elements.append(Image("doctor_signature.png", width=2*inch, height=1*inch))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Image(qr_filename, width=1.5*inch, height=1.5*inch))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("This AI-generated report is for screening purposes only.", style))

        doc.build(elements)

        with open(pdf_filename, "rb") as f:
            st.download_button("📥 Download Certified Report (PDF)", f, file_name=pdf_filename)

    # ---------------- VIEW PAST REPORTS (FOR BOTH ROLES) ---------------- #
    st.markdown("---")
    st.subheader("📂 Past Generated Reports")

    cursor.execute("SELECT * FROM reports ORDER BY timestamp DESC")
    rows = cursor.fetchall()

    if rows:
        for row in rows:
            st.write(f"""
            **Patient ID:** {row[0]}  
            **Verification ID:** {row[1]}  
            **Probability:** {row[2]:.2f}%  
            **Category:** {row[3]}  
            **Doctor:** {row[4]}  
            **Date:** {row[5]}  
            ------------------------------
            """)
    else:
        st.info("No reports available yet.")
