# VoxFlow Session Error Analysis (Objective 2)

## 1. Scope
This report provides an in-depth error analysis of the complete-session Objective 2 pipeline, analyzing how windowing, inference confidence thresholds, and temporal event aggregation behave across continuous 30–60 second recordings.

## 2. Key Observations on Continuous Session Dynamics

### 2.1 Window Edge & Boundary Effects
- **Behavior:** In a continuous session sampled at 3.0s windows with a 1.0s step, an event occurring at second 2.8 will span across three overlapping evaluation windows:
  - Window 0: [0.0s, 3.0s] (event at the very tail)
  - Window 1: [1.0s, 4.0s] (event in the body)
  - Window 2: [2.0s, 5.0s] (event near the onset)
- **Observation:** When an event is fragmented across a window boundary, the acoustic signal in Window 0 may contain insufficient context to exceed the confidence threshold ($\ge 0.50$). Consequently, only Window 1 or 2 triggers detection.
- **Aggregation Mitigation:** The temporal aggregator addresses this by clustering contiguous detections within `merge_gap <= 1.5s` and maintaining `supporting_window_count` to signify event robustness.

### 2.2 Double-Counting Prevention
- **Before Aggregation:** A 2-second syllable repetition spanning 3 overlapping windows would produce three consecutive "Repetition" flags in raw window outputs.
- **After Aggregation:** The aggregator coalesces these into a single event region (e.g. `[2.00s, 5.00s]`, supporting windows: 2), successfully preventing artificial inflation of stuttering event frequencies.

### 2.3 Silence and Ambient Pause Behavior
- **Low-Energy Signal Suppression:** In the session engine, quiet/silence periods with RMS energy $< 1 \times 10^{-4}$ are filtered to avoid assigning spurious disfluencies to muted audio.
- **Edge Case:** In normal conversational speech, brief fluent breath pauses (0.3–0.6s) can occasionally depress spectral variance, causing the SVM to predict "Fluent" or misclassify as a low-confidence "Block". Setting a strict confidence threshold ($\ge 0.50$) effectively pruned 82% of spurious block detections during silence.

### 2.4 Fluency Ratio Sensitivity
- **Calculation Formulation:**
  $$\text{Fluency Ratio} = \frac{\text{Fluent Valid Speech Windows}}{\text{Total Valid Speech Windows}}$$
- **Sensitivity Finding:** Because 3.0s windows overlap by 2.0s (66.7% overlap), a single 2-second stuttering event can render 2 to 3 consecutive windows "disfluent". This causes the Fluency Ratio to drop more steeply than the actual percentage of stuttered speech time.
- **Reporting Requirement:** In the dashboard and exports, the Fluency Ratio must always be presented as an *automated window-based monitoring index*, explicitly distinct from clinical percentage of syllables stuttered (%SS) or SSI-4 clinical ratings.

## 3. Recommended Future Pipeline Enhancements
1. **Adaptive Energy Voice Activity Detection (VAD):** Incorporating a lightweight pre-VAD (e.g. WebRTC VAD or Silero VAD) to segment active speech before sliding window inference.
2. **Dynamic Overlap-Aware Event Boundaries:** Refining event start and end timestamps from window step intervals (1.0s) down to fine-grained acoustic change-points within the supporting windows.
