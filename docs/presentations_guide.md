# Presentation Decks Guide

This guide describes the **curated PowerPoint presentations** and speaking assets tracked in the repository under [`presentations/`](file:///c:/Users/ilyas/Desktop/pose%20recognision/presentations). 

These decks are designed to present, explain, and defend the computer vision machine-safety proof of concept (POC) to academic committees or industrial stakeholders.

---

## 1. Safety Defense Slide Deck (Academic/POC Defense)
* **Presentation Deck**: [`machine-safety-defense-presentation.pptx`](file:///c:/Users/ilyas/Desktop/pose%20recognision/presentations/machine-safety-defense-presentation.pptx)
* **Speaker Script (French)**: [`machine-safety-defense-speaker-script.md`](file:///c:/Users/ilyas/Desktop/pose%20recognision/presentations/machine-safety-defense-speaker-script.md)
* **Verification Log**: [`machine-safety-defense-verification.md`](file:///c:/Users/ilyas/Desktop/pose%20recognision/presentations/machine-safety-defense-verification.md)

This is the primary 11-slide presentation designed for the final project defense. It fits a precise **15-minute speaking budget**, organized slide-by-slide:

| Slide | Title / Purpose | Speak Time | Core Artifact to Display |
|---|---|---|---|
| **1** | Main Title & Context | 0:45 | Fixed camera, fixed machine context |
| **2** | The Core Safety Problem | 1:15 | Nuisance alarms vs. delayed stops |
| **3** | Staged Dataset Audit | 1:00 | Event distribution chart |
| **4** | Causal Timeline Annotation | 1:30 | Browser Annotation Tool Interface |
| **5** | Feature Engineering Pipeline | 1:20 | Pipeline & Policy schema diagram |
| **6** | Sequence Architectures | 1:20 | TCN vs. GRU comparison table |
| **7** | Repeated-Split Evaluation | 1:00 | Split-inheritance diagram |
| **8** | Main Empirical Results | 1:30 | Dual operational tradeoff sweep |
| **9** | Fused Policy Modifiers | 1:15 | Attention/PPE crops and rules |
| **10** | Deployment Latency & Limits | 1:20 | Timing budget workflow diagram |
| **11** | Key Contributions & Next Steps | 0:50 | Future 3D multi-camera outline |

---

## 2. French Data-Collection Strategy
* **Presentation Deck**: [`strategie_collecte_donnees_poc_fr.pptx`](file:///c:/Users/ilyas/Desktop/pose%20recognision/presentations/strategie_collecte_donnees_poc_fr.pptx)

A technical presentation in French describing the initial camera placement, staging guidelines, actor protocols, and file naming conventions designed to collect the 73 clips in a consistent and robust manner. It explains the importance of fixed angles, uniform clothing closure setups, and structured attention variations.

---

## 3. Simple Data-Collection & Setup Guidelines (Updated)
* **Presentation Deck**: [`poc_collecte_donnees_simple_fr_updated.pptx`](file:///c:/Users/ilyas/Desktop/pose%20recognision/presentations/poc_collecte_donnees_simple_fr_updated.pptx)

An updated, simplified quick-guide in French designed for field setups. It offers clear visual checklists for positioning the smartphone camera, establishing the machine's Projected Safety Zone, and executing test sequences safely.

---

## 4. Visual Previews & QA Checks
To ensure maximum visual alignment, slide layout quality checkers and PNG previews were compiled under:
* Previews: `presentations/preview/`
* Layout QA Logs: `presentations/qa/layout-quality.txt`

These audits check element boundaries, margins, font sizing, and chart placement to guarantee that the PowerPoint slides render perfectly in high definition.
