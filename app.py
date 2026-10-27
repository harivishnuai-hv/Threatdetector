from __future__ import annotations
import time
from datetime import datetime
import cv2
import streamlit as st
from vision.detector import load_detector, detect_people, draw_detections
from vision.rules import MotionRuleEngine
from storage.database import init_db, create_incident, list_incidents, review_incident, count_incidents

st.set_page_config(page_title="NIVA-SAFE AI | Safety Review Console", page_icon="🛡️", layout="wide")
init_db()

st.title("🛡️ NIVA-SAFE AI")
st.caption("Networked Intelligent Visual Assistance for Safety | Final-year project prototype")
st.info("Experimental warning cues only. This app does not guarantee threat detection, identify attackers, contact emergency services, or replace human judgment.")

@st.cache_resource
def get_model():
    return load_detector()

with st.sidebar:
    st.header("System status")
    st.success("Local prototype ready")
    st.write("**Vision module:** YOLO person detection")
    st.write("**Event module:** Experimental close-pair + motion cue")
    st.write("**Review:** Human operator required")
    st.divider()
    st.subheader("Safe demonstration")
    st.markdown("Use consented participants or authorized footage. Do not stage real violence. Do not use this prototype for real-world emergency dispatch.")

model = None
try:
    model = get_model()
except Exception as exc:
    st.error("Could not load the YOLO model. Check your internet connection on first run, then restart the app.")
    st.code(str(exc))

left, right = st.columns([1.4, 1])
with left:
    st.subheader("1. Camera / video analysis")
    mode = st.radio("Input source", ["Live webcam scan", "Upload video"], horizontal=True)
    if mode == "Live webcam scan":
        seconds = st.slider("Scan duration (seconds)", 5, 30, 10, 5)
        camera_index = st.selectbox("Camera device", [0, 1, 2], index=0, help="Try 1 if the built-in webcam does not open.")
        if st.button("▶ Start webcam scan", type="primary", disabled=model is None, use_container_width=True):
            cap = cv2.VideoCapture(int(camera_index), cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(int(camera_index))
            if not cap.isOpened():
                st.error("Webcam could not be opened. Close Camera/Teams/Zoom and check Windows camera permissions.")
            else:
                engine = MotionRuleEngine()
                preview = st.empty()
                status = st.empty()
                progress = st.progress(0)
                started = time.time()
                frame_count = 0
                last_event_time = 0.0
                latest_cues = []
                while time.time() - started < seconds:
                    ok, frame = cap.read()
                    if not ok:
                        status.warning("Camera stopped returning frames.")
                        break
                    frame_count += 1
                    detections = detect_people(model, frame)
                    cues, diagnostics = engine.update(frame, detections)
                    latest_cues = cues
                    annotated = draw_detections(frame, detections)
                    if cues:
                        cv2.putText(annotated, "REVIEW CUE: POSSIBLE ALTERCATION", (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
                    rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    preview.image(rgb, channels="RGB", use_container_width=True)
                    elapsed = time.time() - started
                    progress.progress(min(1.0, elapsed / seconds))
                    status.write(f"Elapsed: {int(elapsed)}s / {seconds}s | People detected: {len(detections)} | Frames analysed: {frame_count}")
                    # Save a single incident per scan when a heuristic persists.
                    if cues and time.time() - last_event_time > 8:
                        details = "; ".join(cues)
                        create_incident("POSSIBLE ALTERCATION CUE", "Experimental motion heuristic", details, "PENDING")
                        last_event_time = time.time()
                    time.sleep(0.015)
                cap.release()
                progress.progress(1.0)
                status.success("Scan complete. Review any generated event in the Incident Review section below.")
                st.caption("Latest diagnostic: " + (", ".join(latest_cues) if latest_cues else "No heuristic cue triggered during this scan."))
    else:
        uploaded = st.file_uploader("Upload a consented MP4 / AVI video", type=["mp4", "avi", "mov", "mkv"])
        max_seconds = st.slider("Maximum analysis duration (seconds)", 5, 60, 20, 5)
        if uploaded is not None and st.button("Analyze uploaded video", type="primary", disabled=model is None, use_container_width=True):
            import tempfile, os
            suffix = "." + uploaded.name.split(".")[-1]
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getbuffer())
                    temp_path = tmp.name
                cap = cv2.VideoCapture(temp_path)
                if not cap.isOpened():
                    st.error("Could not read this video file.")
                else:
                    engine = MotionRuleEngine()
                    preview = st.empty()
                    progress = st.progress(0)
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25
                    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                    max_frames = min(total if total else int(fps * max_seconds), int(fps * max_seconds))
                    n = 0
                    last_event_frame = -999999
                    any_cue = False
                    while n < max_frames:
                        ok, frame = cap.read()
                        if not ok: break
                        n += 1
                        detections = detect_people(model, frame)
                        cues, diagnostics = engine.update(frame, detections)
                        annotated = draw_detections(frame, detections)
                        if cues:
                            any_cue = True
                            cv2.putText(annotated, "REVIEW CUE: POSSIBLE ALTERCATION", (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
                            if n - last_event_frame > int(fps * 8):
                                create_incident("POSSIBLE ALTERCATION CUE", "Experimental motion heuristic", "; ".join(cues), "PENDING")
                                last_event_frame = n
                        preview.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                        progress.progress(min(1.0, n / max(1, max_frames)))
                    cap.release()
                    st.success(f"Video analysis complete. Analysed {n} frames. Heuristic cue observed: {'Yes' if any_cue else 'No'}.")
            except Exception as exc:
                st.error(f"Video processing failed: {exc}")
            finally:
                if temp_path and os.path.exists(temp_path): os.unlink(temp_path)

with right:
    st.subheader("2. Quick safety controls")
    st.markdown("A manual SOS is a **demonstration event**. It does not send a real emergency notification.")
    sos_note = st.text_input("Optional operator note", placeholder="e.g., test SOS for faculty demo")
    if st.button("🆘 Simulate manual SOS", use_container_width=True):
        create_incident("MANUAL SOS (DEMO)", "Operator initiated", sos_note.strip() or "Manual SOS test event", "PENDING")
        st.success("Demo SOS logged. Review it below.")
    st.metric("Total incidents logged", count_incidents())
    st.metric("Pending reviews", count_incidents(status="PENDING"))
    st.caption("Only event metadata is stored; this prototype does not save video frames to the database.")

st.divider()
st.subheader("3. Incident review console")
records = list_incidents(limit=50)
if not records:
    st.info("No incidents yet. Run a scan or simulate an SOS to populate the review queue.")
else:
    for incident in records:
        iid, timestamp, category, source, details, status_value, reviewer_note = incident
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.markdown(f"**#{iid} · {category}**")
            c1.caption(timestamp)
            c2.write(f"**Source:** {source}")
            c2.write(details)
            c3.write(f"**Status:** {status_value}")
            if status_value == "PENDING":
                note = st.text_input("Review note (optional)", key=f"note_{iid}", placeholder="Reason for decision")
                b1, b2 = st.columns(2)
                if b1.button("Confirm for demo", key=f"confirm_{iid}"):
                    review_incident(iid, "CONFIRMED (DEMO)", note)
                    st.rerun()
                if b2.button("Reject / false alarm", key=f"reject_{iid}"):
                    review_incident(iid, "REJECTED", note)
                    st.rerun()
            elif reviewer_note:
                st.caption(f"Review note: {reviewer_note}")

st.divider()
st.subheader("4. Prototype boundaries")
st.markdown("""
- Person detection is not threat detection.
- The altercation cue is an unvalidated visual-motion heuristic, not a trained fight classifier.
- It can miss real incidents and produce false alarms (e.g., sports, dancing, crowd motion, occlusion, or camera shake).
- Being alone, being a woman, clothing, or proximity alone must never be treated as evidence of danger.
- No face recognition, automatic police dispatch, or physical siren is connected.
""")
