# HEAR-UI — User Manual

<p align="center">
  <img height="120px" src="frontend/public/assets/images/Logo.png" alt="HEAR-UI Logo">
</p>

> **HEAR-UI** is an AI-powered clinical decision support tool for estimating cochlear implant outcomes.  
> This manual explains how clinicians can use the web interface to manage patients, obtain predictions, interpret explanations, and provide feedback.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Searching for Patients](#searching-for-patients)
3. [Creating a New Patient](#creating-a-new-patient)
4. [Viewing Patient Details](#viewing-patient-details)
5. [Obtaining a Prediction](#obtaining-a-prediction)
6. [Interpreting SHAP Explanations](#interpreting-shap-explanations)
7. [What-if Analysis](#what-if-analysis)
8. [Providing Feedback](#providing-feedback)
9. [Model Card](#model-card)
10. [Language Switching](#language-switching)
11. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Getting Started

1. Open the application in your browser at **http://localhost:5173** (or the URL provided by your administrator).
2. The landing page displays the patient search interface.
3. No login is required — the system is designed for use within a secure clinical network.

> **Important:** HEAR-UI is a **decision support tool**. All predictions are estimates and must be evaluated by a qualified medical professional. The final clinical decision always rests with the treating physician.

---

## Searching for Patients

<p align="center">
  <img width="700px" src="frontend/public/assets/images/search.png" alt="Patient Search">
</p>

1. On the main page, type a patient's **name** (first or last) into the search field.
2. Matching patients appear in real time as you type.
3. Click on a patient row to open their detail view.
4. If no patient is found, you can create a new one (see below).

---

## Creating a New Patient

<p align="center">
  <img width="700px" src="frontend/public/assets/images/add_patient.png" alt="Add New Patient">
</p>

1. Click the **"Add Patient"** button from the search view.
2. Fill in the patient data form. Fields are organized by category:
   - **Demographics** — Gender, age at implantation
   - **Pre-operative symptoms** — Tinnitus, vertigo, taste disturbance, etc.
   - **Imaging findings** — MRI/CT results, anatomical anomalies
   - **Audiological data** — Late latency responses, thresholds
   - **Hearing history** — Duration of hearing loss, previous hearing aids
   - **Implant details** — Manufacturer, electrode type
   - **Outcome measurements** — Pre- and post-operative scores
3. Required fields are marked. Inline validation highlights any errors.
4. Click **"Save"** to create the patient record.

> **Tip:** Fields use German-language names matching clinical documentation standards. Switch to English using the language toggle if needed.

---

## Viewing Patient Details

After selecting a patient, the **detail view** displays all stored clinical data grouped by category:

- Demographics and implant information
- Pre-operative symptoms and imaging findings
- Audiological measurements and hearing history
- Outcome measurements

From this view, you can:
- **Edit** patient data using the edit button
- **Request a prediction** using the predict button
- **Delete** the patient record

---

## Obtaining a Prediction

<p align="center">
  <img width="700px" src="frontend/public/assets/images/prediction.png" alt="Prediction View">
</p>

1. From the patient detail view, click **"Predict"**.
2. The system sends the patient's data to the AI model and returns:
   - **Success probability** — displayed as a percentage (e.g., 68%)
   - **Decision threshold curve** — visual indicator of where this patient falls
   - **Classification label** — "Successful" or "Limited improvement"
3. The prediction appears in real time (typically under 100 ms).

### Understanding the Probability

| Probability | Interpretation |
|-------------|----------------|
| > 70% | High likelihood of significant improvement |
| 40–70% | Moderate — further clinical assessment recommended |
| < 40% | Lower likelihood — discuss carefully with the patient |

> **Note:** The model was trained on N=235 patients from a single institution. Probabilities are estimates and should be interpreted alongside clinical expertise and patient-specific factors.

---

## Interpreting SHAP Explanations

Below the prediction, a **SHAP feature importance chart** shows which patient attributes influenced the prediction most:

- **Red bars** (positive) push the prediction **toward** success
- **Blue bars** (negative) push the prediction **away from** success
- The length of each bar indicates the **magnitude** of influence

**Example interpretation:**
> "Pre-operative speech score = 45% contributes +0.12 to the success probability, while hearing loss duration = 15 years contributes −0.08."

The top 5 most influential features are shown by default. This helps clinicians understand *why* the model made a specific prediction and verify whether the reasoning aligns with their clinical judgment.

### Alternative Explanation Methods

The system supports three explanation methods:
- **SHAP** (default) — theoretically grounded feature attributions
- **LIME** — local interpretable model-agnostic explanations
- **Coefficient-based** — simpler linear attribution

---

## What-if Analysis

The **What-if tool** allows you to explore hypothetical scenarios:

1. From the prediction view, click **"What-if Analysis"**.
2. Modify individual patient features (e.g., change age, implant type, or hearing loss duration).
3. The model recalculates the prediction in real time.
4. Compare the original and modified predictions side by side.

This is useful for understanding how changes in patient characteristics would affect the predicted outcome.

---

## Providing Feedback

After reviewing a prediction, clinicians can submit feedback:

1. Click **"Agree"** (thumbs up) or **"Disagree"** (thumbs down) to indicate whether the prediction aligns with your clinical assessment.
2. Optionally add a **free-text comment** explaining your reasoning.
3. Click **"Submit"** to save the feedback.

Feedback is stored in the database linked to the specific prediction. It is used for:
- Monitoring model performance over time
- Identifying systematic errors
- Supporting future model improvements

---

## Model Card

The **Model Card** provides full transparency about the AI model:

- **Model type:** Random Forest classifier (100 trees)
- **Training data:** N=235 patients, 39 features
- **Performance:** Accuracy 62%, F1 0.55 (5-fold cross-validation)
- **Intended use:** Decision support for cochlear implant candidacy
- **Limitations:** Single-institution training data, moderate accuracy
- **Ethical considerations:** Not a replacement for clinical judgment

Access the Model Card via the navigation menu or the API at `/api/v1/model-card`.

---

## Language Switching

HEAR-UI supports **German** and **English**:

- Click the language toggle (DE / EN) in the navigation bar
- All labels, field names, and interface text switch automatically
- Patient data field names follow German clinical terminology by default

---

## FAQ & Troubleshooting

### The prediction shows a very high or low probability. Should I trust it?

Probabilities are clipped to the range 1%–99% by design to prevent overconfident predictions. Extreme values still indicate strong model confidence but should always be verified clinically.

### A patient's data is incomplete. Can I still get a prediction?

Yes. Missing fields are filled with sensible clinical defaults. However, predictions are more reliable when all fields are provided.

### The SHAP chart shows unexpected feature importance. Why?

SHAP values reflect *this specific patient's* prediction, not general feature importance. A normally unimportant feature may have high attribution for an unusual patient. If the explanation seems implausible, consider providing feedback through the feedback interface.

### How do I report a bug or request a feature?

Contact the development team or file an issue on the project's GitHub repository.

### The application is not loading.

1. Verify that the Docker containers are running: `docker compose ps`
2. Check the backend health: `curl http://localhost:8000/api/v1/utils/health-check/`
3. Clear your browser cache and try again
4. Check the browser console (F12) for error messages

---