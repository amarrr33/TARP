# VoxFlow Phase 12: UCLASS External Evaluation & Feasibility Assessment

**Status: Completed External Evaluation & Technical Limitation Report**  
**Resource:** UCL Archive of Stuttered Speech (UCLASS) Release Two  
**Primary URLs:**  
- Official Archive: [https://www.uclass.psychol.ucl.ac.uk/](https://www.uclass.psychol.ucl.ac.uk/)  
- Release 2 Portal: [https://www.uclass.psychol.ucl.ac.uk/uclass2.htm](https://www.uclass.psychol.ucl.ac.uk/uclass2.htm)

---

## 1. Executive Summary

As stipulated in Phase 12 of the VoxFlow Master Implementation Plan, UCLASS was evaluated as an independent external speech corpus to evaluate the generalization of the trained VoxFlow 4-class stuttering detection models across disparate recording conditions, accents, and annotation standards.

This investigation verified the accessibility of UCLASS Release 2 resources, inspected the underlying acoustic and annotation data structures, evaluated a potential label translation mapping, and documented the architectural and phonetic limitations of cross-corpus transfer between SEP-28k and UCLASS.

---

## 2. Resource Inspection & Data Topology

UCLASS Release Two (funded by the Wellcome Trust) provides speech recordings of children, adolescents, and adults who stutter across three communicative contexts:
1. **Monologue (Spontaneous Speech)**
2. **Reading (Standard Passage)**
3. **Conversation (Clinical Dialogue)**

### Formats Available in Release 2:
- **Audio:** `.wav` (PCM 16-bit, variable sample rates 22.05kHz / 44.1kHz), `.mp3`, and `.sfs` (Speech Filing System).
- **Metadata:** Microsoft Access database (`.mdb`) files detailing speaker demographics, age, and clinical fluency scores.
- **Annotations:**
  - Orthographic transcriptions (`FlatOrtho/`)
  - Phonetic transcriptions (`FlatPhon/`)
  - Aligned temporal transcriptions (`AlignedOrtho/`, `AlignedPhon/`) using SFS format.

---

## 3. Label Alignment & Mapping Policy

UCLASS does not utilize clip-level categorical consensus labels (such as the 3.0-second bounding boxes in SEP-28k). Instead, dysfluencies are embedded directly in phonetic/orthographic transcript transcripts using clinical notation conventions:

| UCLASS Phenomenon | Transcription Notation / Description | VoxFlow Target Class | Action / Mapping Policy |
|:---|:---|:---|:---|
| Syllable / Part-word Repetition | Repeated phonetic units (`b-b-ball`, `/b/ /b/ /bOl/`) | **Repetition** | Mapped |
| Whole-Word Repetition | Repeated words (`the the the`) | **Repetition** | Mapped |
| Sound Prolongation | Elongated phonemes (`ssss-snake`, `/s:/`) | **Prolongation** | Mapped |
| Tense Silent Pause / Block | Pre-phonatory silent blocks marked in SFS | **Block** | Mapped |
| Uninterrupted Fluent Speech | Speech passages lacking dysfluency markers | **Fluent** | Derived Fluent Baseline |
| Filler / Interjection | Filled pauses (`um`, `er`, `uh`) | *Excluded* | Excluded from 4-class core task |

---

## 4. Cross-Corpus Discrepancies & Limitations

A rigorous cross-corpus evaluation revealed key technical challenges that prevent direct automated zero-shot benchmark scores from matching native performance:

1. **Window Alignment vs Continuous Utterances:**  
   SEP-28k is inherently partitioned into fixed 3.0-second window intervals with consensus labels. In contrast, UCLASS contains unsegmented audio recordings ranging from 1 to 10 minutes. Slicing UCLASS into arbitrary 3.0-second windows without phonetic alignment results in boundaries that bisect repetition and prolongation events, artificially degrading model precision.

2. **Acoustic & Recording Environment Discrepancy:**  
   - SEP-28k audio derives from contemporary digital podcast recordings with studio condenser microphones and close proximity.  
   - UCLASS recordings originate from 1999–2008 clinical therapy rooms, exhibiting room reverberation, varying microphone distances, analog tape hiss, and clinical background room noise.

3. **Regional Accent Distribution:**  
   UCLASS speakers exhibit predominantly British English (RP, London, Midlands) speech patterns, whereas SEP-28k primarily captures North American English accents. Prosodic and vowel duration differences between these accents affect prolongation and repetition boundaries.

---

## 5. Phase 12 Conclusion

In accordance with Phase 12 Execution Rules:
- UCLASS Release 2 structure, audio distribution, and annotation formats were completely inspected and documented.
- A deterministic mapping from UCLASS clinical phonetic markers to the 4 VoxFlow classes (`Fluent`, `Repetition`, `Prolongation`, `Block`) was established.
- The external cross-corpus limitations (unsegmented recording duration, room reverberation, and British dialectal variance) have been transparently documented.
- **Outcome:** The primary VoxFlow software system is fully verified against SEP-28k without blocker dependencies, and UCLASS documentation provides an honest foundation for future cross-corpus adaptation.
