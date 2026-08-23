# 🏁 TrackPulse

### Live Track Condition Detector

TrackPulse is a lightweight computer-vision based application that analyzes racing track images and estimates the current track condition as **Dry, Damp, Wet, or Drying**.

The goal is simple: help a race team understand whether track conditions are improving or getting worse and provide a quick **tire strategy suggestion**.

---

## 🚀 What TrackPulse Does

TrackPulse takes a trackside or onboard image and looks for visual clues such as:

* ☀️ Brightness
* 🎨 Color saturation
* 💧 Reflections and glare
* 🛣️ Surface texture
* 🌑 Darkness

These features are combined to calculate a **Wetness Score from 0–100**.

The score is then converted into a simple condition:

| Wetness Score | Condition |
| ------------- | --------- |
| 0–27          | 🟢 Dry    |
| 28–51         | 🟡 Damp   |
| 52–100        | 🔵 Wet    |

TrackPulse also compares the current reading with recent frames. This allows it to detect a **drying trend** instead of looking at every image independently.

---

## 🧠 How the Model Works

TrackPulse uses a **hybrid Computer Vision + Rule-Based approach**.

It does not depend on a large pretrained AI model. Instead, it uses image processing and interpretable mathematical rules, making it lightweight and easy to run.

### Step 1 — Image Processing

The uploaded image is resized and converted into different image representations using **Pillow and NumPy**.

### Step 2 — Feature Extraction

The system extracts four main features:

**1. Brightness**

Measures how bright the image is.

**2. Saturation**

Measures the strength of colors in the image.

**3. Specular Highlight Ratio**

Detects very bright and low-saturation pixels.

These can represent reflections or glare from a wet surface.

**4. Edge Density**

Measures how much texture/detail is visible on the track.

A wet surface can appear smoother because reflections reduce visible surface texture.

---

## 📊 Wetness Score

The extracted features are normalized and combined using weighted rules.

The current scoring gives the largest importance to reflections/glare, followed by surface texture and darkness.

Simplified:

```text
Wetness Score =
    45% × Reflection/Glare
  + 35% × Surface Smoothness
  + 20% × Darkness
```

The final score is limited to a range of **0–100**.

This makes the result easy to understand and display to a race engineer.

---

## 📈 Drying Trend Detection

A single image is not always enough to understand track evolution.

TrackPulse therefore keeps a short history of previous readings.

It compares the current wetness score with the recent average.

For example:

```text
Frame 1 → 78  → Wet
Frame 2 → 71  → Wet
Frame 3 → 61  → Wet
Frame 4 → 48  → Drying
Frame 5 → 35  → Drying
```

Instead of simply saying "Damp", the system can recognize that the track is **getting drier**.

This is useful for identifying a possible tire-change window.

---

## 🏎️ Tire Strategy Suggestions

Based on the detected condition and trend, TrackPulse provides a simple recommendation.

Examples include:

* **Dry and stable** → Slicks are suitable
* **Drying** → Tire-change window may be approaching
* **Damp and getting wetter** → Consider intermediates
* **Wet** → Full wets/intermediates may be required
* **Wet but improving** → Monitor the drying trend

These are decision-support suggestions, not guaranteed race strategy decisions.

---

## 🖥️ Application

The user interface is built using **Streamlit**.

Users can:

* 📤 Upload one or multiple track images
* 📷 Capture an image using the camera
* 🎯 View the current track condition
* 📊 See the wetness score
* 📈 Monitor the track condition trend
* 🗂️ View the frame history
* ⬇️ Download the analysis as a CSV file

Multiple uploaded images can be treated as sequential frames, allowing the application to simulate a short video sequence.

---

## 📂 Project Structure

```text
TrackPulse/
│
├── app.py              # Streamlit user interface
├── analyzer.py         # Core computer vision and classification logic
├── styles.css          # Custom application styling
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

### `analyzer.py`

Contains the main `TrackConditionAnalyzer` class.

It handles:

* Image feature extraction
* Wetness score calculation
* Dry/Damp/Wet classification
* Drying trend detection
* Tire strategy suggestions

### `app.py`

Handles the Streamlit application.

It manages:

* Image uploads
* Camera input
* Session history
* Results display
* Trend visualization
* CSV export

### `styles.css`

Contains the custom styling used to make the Streamlit interface more visually engaging.

### `requirements.txt`

Contains the main dependencies:

* Streamlit
* NumPy
* Pandas
* Plotly
* Pillow

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/Jiya404/TrackPulse.git
cd TrackPulse
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---

## 🔄 Basic Workflow

```text
Track Image
     ↓
Image Preprocessing
     ↓
Feature Extraction
     ↓
Wetness Score (0–100)
     ↓
Dry / Damp / Wet
     ↓
Compare With Previous Frames
     ↓
Detect Trend
     ↓
Race/Tire Strategy Suggestion
```

---

## 🛠️ Technologies Used

* **Python**
* **Streamlit**
* **NumPy**
* **Pillow**
* **Pandas**
* **Plotly**
* **Computer Vision**
* **Rule-Based Classification**

---

## 🎯 Why This Approach?

TrackPulse was designed to be:

* ⚡ Lightweight
* 🧠 Easy to understand
* 📦 Easy to deploy
* 🔍 Interpretable
* 📊 Easy to visualize
* 🚀 Fast enough for interactive use

Instead of requiring a large deep-learning model, TrackPulse uses explainable visual features and scoring rules.

This also makes it easier to understand **why** a particular track condition was predicted.

---

## 🔮 Future Improvements

Possible future improvements include:

* 🎥 Real-time video analysis
* 🏎️ Live trackside camera integration
* 🌦️ Weather API integration
* 🧠 Training a machine-learning model on real racing track images
* 📍 Multi-camera track monitoring
* ⏱️ Real-time tire-change alerts
* 📊 Historical race-condition analysis
* 🏁 Integration with live race telemetry

---

## ⚠️ Disclaimer

TrackPulse is a prototype decision-support tool created for a hackathon/project environment.

Its predictions are based on visual image features and rule-based scoring and should **not be treated as a replacement for professional race engineering, weather data, track sensors, or official race telemetry**.

---

## 👩‍💻 Author

**Jiya404**

## ⭐ Project Summary

**TrackPulse turns track images into a simple, understandable racing insight:**

> **"How wet is the track, is it getting better or worse, and what should we consider doing next?"**

🏁 **TrackPulse — Read the track. React before it changes.**
