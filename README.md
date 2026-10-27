# NIVA-SAFE AI

**Full project name:** Networked Intelligent Visual Assistance for Safety using AI and Computer Vision.

A structured final-year B.Tech prototype for person detection, experimental possible-altercation review cues, a manual demo SOS control, and a persistent SQLite incident review console.

## Important accuracy and safety statement

No system can guarantee 100% detection of every threat in every environment. This prototype does **not** have a trained all-threat classifier. Its experimental possible-altercation cue combines two nearby person detections with high frame-to-frame visual change in the shared region over several updates. It may miss real incidents and produce false alarms. A person being alone, being a woman, clothing, or proximity by itself is not evidence of danger. All alerts require human review. The manual SOS is simulated; this application does not contact police, emergency services, or a physical siren.

## Features

- Live webcam scan (Windows DirectShow first, then default OpenCV backend)
- Uploaded video analysis
- YOLOv8 nano person detection and bounding boxes
- Experimental close-pair + motion heuristic for a *possible altercation review cue*
- Manual simulated SOS button
- SQLite incident records with pending / confirmed-demo / rejected review statuses
- Separated detector, rule engine, persistence, and UI modules
- Basic test for the rule engine

## Folder structure

```text
niva_safe_project/
├── app.py
├── requirements.txt
├── README.md
├── vision/
│   ├── __init__.py
│   ├── detector.py
│   └── rules.py
├── storage/
│   ├── __init__.py
│   └── database.py
├── tests/
│   └── test_rules.py
└── docs/
    ├── ARCHITECTURE.md
    ├── TEST_PLAN.md
    └── FACULTY_DEMO.md
```

## Requirements

- Windows 10/11
- Python 3.10 or 3.11 recommended
- Internet connection for dependency installation and the first YOLO weights download
- Webcam or a video clip that you have permission to use

## Install and run (Windows Command Prompt)

Open Command Prompt in this project folder and run one command at a time:

```bat
python --version
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`. On the first launch, Ultralytics may download `yolov8n.pt`; allow the download to finish.

## Webcam troubleshooting

1. Close Windows Camera, Teams, Zoom, and other apps using the camera.
2. Open **Settings → Privacy & security → Camera** and enable camera access and desktop-app access.
3. Try camera device 1 in the sidebar if device 0 fails.
4. If Streamlit reports the port is occupied, run `python -m streamlit run app.py --server.port 8502`.
5. If the YOLO weights cannot download, verify network access and retry.

## Testing

Install dependencies first, then run:

```bat
python -m unittest discover -s tests -v
```

The included test only checks the heuristic's basic behavior; it is not an accuracy evaluation. See `docs/TEST_PLAN.md` for a validation plan.

## Suggested evaluation metrics

Use a labelled test set separate from any tuning data and report: precision, recall, F1, false alarms per minute, missed-event rate, event-level detection delay, and FPS. Report results by lighting, distance, occlusion, crowd density, and camera angle. Never advertise a result as 100% without an appropriately large, representative, independently evaluated test set—and even then, do not imply future perfect performance.

## Privacy and deployment

Use consented participants or authorized footage. Prefer local processing, do not add face recognition without a specific justified requirement and legal/privacy review, limit retention, restrict dashboard access, and maintain an audit trail before any pilot. Do not connect this student prototype to public CCTV, sirens, or emergency dispatch without written authorization and a safety review.
