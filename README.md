[![CI](https://github.com/aayuushh365/sprintSense/actions/workflows/ci.yml/badge.svg)](../../actions)
# SprintSense  
*A lightweight sprint analytics and predictive delivery intelligence tool.*

<img src="./assets/ChatGPT Image Nov 20, 2025, 09_19_26 PM.png" width="160" />

## Overview
SprintSense is a streamlined analytics platform designed to help product teams understand how they are performing and forecast how likely they are to meet upcoming sprint commitments.  
It blends agile delivery metrics, predictive modeling, and narrative insights into a single, easy to use dashboard.

The goal is to give product managers, engineering managers, and teams an objective way to reason about velocity, predictability, quality, and future outcomes without spreadsheets or guesswork.

---

## Key Features
### Predictive engine
- Monte Carlo simulation estimating probability of completing next sprint's commitment.  
- Adjustable inputs: number of historical sprints, planned commitment, simulation count, random seed.  
- Visualization of velocity distribution vs commitment line.  
- Summary table with probability thresholds.

### Insights engine
- Automated narrative insights for:  
  - Velocity  
  - Carryover  
  - Predictability  
  - Defects and quality  
  - Cycle time  
- High level signal cards  
- Detailed expandable explanations

### Team profile inference
- Sprint cadence estimation  
- Approximate team size  
- Average velocity and variation  
- Predictability summary derived from carryover

### UI and usability
- Clean, minimal Streamlit layout  
- Sidebar settings for simulation and insights  
- Screenshot-ready visualizations  
- Designed for portfolio demonstration and hiring manager review

---

## Architecture

```
SprintSense
|-- app/
|   |-- pages/
|   |   |-- 01_Overview.py
|   |   |-- 02_Trends.py
|   |   |-- 03_Completion_Probability.py
|   |   |-- 04_Team_Insights.py
|   |
|   |-- lib/
|   |   |-- data_access.py
|   |   |-- kpis.py
|   |   |-- schema.py
|   |
|-- data/
|   |-- sample_sprint.csv
|
|-- README.md
|-- requirements.txt
```

### Core components
- **kpis.py**  
  Computes velocity, throughput, carryover rate, defect ratio, and cycle time.
- **Completion Probability**  
  Runs Monte Carlo simulation using historical velocity samples.
- **Team Insights**  
  Multi-metric reasoning engine with narrative output.
- **Team Profile**  
  Automated inference of cadence, team size, average velocity, and predictability.

---

## Installation

```
git clone https://github.com/<your_username>/sprintsense.git
cd sprintsense
pip install -r requirements.txt
```

## Running the app

```
streamlit run app/Home.py
```

The app will open in your browser at:

```
http://localhost:8501
```

---

## Screenshots

Add your exported screenshots into `/docs/screenshots/` and reference them here.

Example:

```
![Completion Probability](docs/screenshots/completion_probability.png)
![Team Insights](docs/screenshots/team_insights.png)
![Velocity Distribution](docs/screenshots/velocity_distribution.png)
```

---

## Why this project matters
Engineering teams struggle to get a consistent picture of velocity, predictability, and quality across sprints. Most tools dump raw data without context. SprintSense reframes agile metrics into decision-ready insights.

This project demonstrates:
- End-to-end product thinking  
- Data modeling  
- Predictive simulation  
- Narrative analytics  
- UI design and usability  
- Real-world PM perspective on engineering data

---

## Roadmap

### Near term
- Custom CSV uploads  
- Multi-team comparison  
- Better sprint timeline visualizations

### Longer term
- JIRA API integration  
- Predictions based on cycle time distribution  
- Confidence band visualization  
- Quality risk alerts

---

## License
MIT License

