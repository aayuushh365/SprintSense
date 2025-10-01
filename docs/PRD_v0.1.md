# SprintSense — PRD v0.1

# Product Requirement Doc (PRD v0.1)

# Problem

Product Managers, PMOs, and Program Managers struggle to get a clear, reliable view of sprint health. Existing tools (e.g., Jira dashboards) present raw metrics but fail to provide synthesized, decision-ready insights. This results in:

- Time wasted manually exporting data to spreadsheets.
- Confusion from inconsistent team practices and labeling.
- Lack of early warning signals mid-sprint.
- Metrics that don’t connect to business outcomes, leading to low trust from leadership.

### **Who experiences this issue?**

- PMs responsible for 1–4 teams (Alex, Miguel).
- PMO leads overseeing 10+ teams (Priya).
- Program managers coordinating global releases (Sarah).

### **When does it occur?**

- Mid-sprint (need progress signals).
- End-of-sprint (need to reconcile planned vs. delivered).
- During quarterly/executive reporting (need cross-team consistency).

### **Research basis**

Since I don’t yet have direct customer interviews, I simulated **four realistic product manager personas** using ChatGPT, each with different contexts:

- Alex (Senior PM, SaaS platform).
- Priya (PMO Lead, Enterprise IT).
- Miguel (Product Owner, Startup AI).
- Sarah (Program Manager, Global fintech).

This gave me qualitative “interview notes” highlighting pain points and trusted metrics.

### **Why urgent/important?**

Without trustworthy sprint analytics, planning confidence is low, teams overcommit, and leadership lacks visibility. Improving predictability directly reduces wasted time and increases delivery confidence.

---

# 💭 Proposal

### **How are we solving this issue?**

By building **SprintSense**, a lightweight Streamlit app that ingests Jira-style CSV data and generates trusted KPIs: velocity, throughput, carryover, cycle/lead time, defect ratio, and WIP trends.

### **Why this approach?**

- **Alternatives considered:** Use built-in Jira dashboards, Tableau reports, or Excel spreadsheets. These are either too generic (Jira), too heavy (Tableau), or too manual (Excel).
- **Chosen approach:** Start with Streamlit for speed and accessibility, allowing rapid iteration and deployment.

### **General shape of the solution:**

- Upload CSV → Validate schema → Compute KPIs → Show dashboards → Export status summary.
- Modular design (UI, metrics, data layer separated) so it can later connect to live Jira API or a database.

### **Measures of success:**

- Time saved (less manual reporting).
- Consistency across teams (same schema, same KPIs).
- Clarity (fewer charts, clearer signals).

### **Fast, scalable, low-cost:**

- Runs in Streamlit Cloud initially.
- Low infra cost, pure Python stack.
- Can scale later with DB integrations.

---

# 🛫 Plan

### **What are we building?**

- A KPI analytics dashboard for agile teams.
- Mid-sprint and end-sprint views.
- Exportable insights for leadership decks.

### **How does it work?**

- CSV ingestion + validation.
- Metric computation with Pandas.
- Visualization in Streamlit.
- Caching for performance.

### **How do we know it works?**

- Unit tests for KPI functions.
- User testing with synthetic datasets.
- Later: compare with real Jira exports.

### **What are we measuring?**

- Accuracy of metrics (vs. manual calc).
- Speed to produce a sprint health report.
- User trust/clarity via feedback.

### **When will it be ready?**

- Week 0.5: Repo + skeleton ✅
- Week 1: Problem research + PRD (current).
- Week 2: Personas + JTBD + KPI definitions.
- Week 3: Synthetic data + charts.
- Week 4: Export features + polish.
- Week 5–6: Deployment + portfolio write-up.

# Personas

**Alex — Senior PM (SaaS platform)**

- **Context:** Oversees 4 cross-functional teams in a growing SaaS company. Heavy reliance on Jira dashboards, but frustrated by inconsistency.
- **Goals:** Improve mid-sprint visibility, reduce manual reporting time, ensure teams hit commitments.
- **Pains:** Inconsistent labeling, too many charts without clarity, spends ~45 mins weekly building manual reports.
- **Success criteria:** 3 key signals per sprint, ability to quickly explain velocity dips to stakeholders, less time in spreadsheets.

**Priya — PMO Lead (Enterprise IT)**

- **Context:** Manages 12 agile teams across a large IT org. Responsible for exec reporting and predictability metrics.
- **Goals:** Provide leadership with consistent, reliable roll-ups. Ensure delivery predictability across teams.
- **Pains:** Inconsistent team data, manual Excel consolidation, velocity charts without context, time wasted building quarterly decks.
- **Success criteria:** Consistent KPI definitions across teams, clear link between velocity and defect ratios, faster preparation of quarterly reviews.

**Miguel — Product Owner (Startup AI product)**

- **Context:** Handles backlog for 2 scrums in a resource-constrained AI startup. Minimal tooling, pragmatic approach.
- **Goals:** Keep sprints on track, manage scope creep, balance features vs. bug fixes.
- **Pains:** Burndown charts misleading, bugs derail features, metrics feel like vanity numbers.
- **Success criteria:** Reliable carryover tracking, quick view of bug/feature trade-offs, actionable insights at daily stand-ups.

**Sarah — Program Manager (Global fintech)**

- **Context:** Coordinates multi-geo teams, compliance-critical deliverables. Reports to leadership on both progress and risks.
- **Goals:** Ensure compliance deadlines are met, surface risks early, present metrics that resonate with executives.
- **Pains:** Metrics don’t highlight risks early, cycle time skewed by outliers, inconsistent team labeling, dashboards disconnected from business outcomes.
- **Success criteria:** Early warning system for slippage, defect ratio visibility, metrics tied directly to business impact so execs listen.

# KPI Tree

**North Star:** *Time to Confident Sprint Decision (TCD)* — minutes to produce and communicate an accurate sprint health verdict.

![Untitled diagram _ Mermaid Chart-2025-10-01-035031.svg](attachment:5f9df3f7-dd8d-4758-b81f-03b6413684b5:Untitled_diagram___Mermaid_Chart-2025-10-01-035031.svg)

**Definitions**

- **Velocity variance:** StdDev(velocity)/Mean(velocity) over last 6 sprints.
- **Carryover rate:** Unfinished at sprint end ÷ committed at sprint start.
- **Throughput stability:** CoV of issue count over last 6 sprints.
- **Cycle/Lead time:** Resolved−In‑Progress start / Resolved−Created.
- **Defect ratio:** Bugs ÷ all resolved issues in sprint.

### OKRs

**Objective 1 — Ship decision-ready sprint signals**

- **KR1:** Reduce TCD from ~45 min manual to **<5 min** by Week 6 using SprintSense.
- **KR2:** Achieve **≥90%** KPI parity vs. manual spreadsheet checks on synthetic data.
- **KR3:** Render 3 core KPI cards in **<2s** on the sample dataset.
- **KR4:** Provide **CSV/PNG exports** from Overview page.

**Objective 2 — Improve predictability insight**

- **KR1:** Display **velocity variance** and **carryover rate** trendlines across 6 sprints.
- **KR2:** Flag mid-sprint risk when **WIP exceeds planned capacity by ≥20%** (rule-based alert).
- **KR3:** Show **defect ratio** with 6-sprint trend and bug/story split.
- **KR4:** Document root-cause lenses (scope churn, staffing, defects) in the PRD and UI copy.

**Objective 3 — Deliver a usable, public MVP**

- **KR1:** Deploy to **Streamlit Cloud** with a public link and README quickstart.
- **KR2:** Add **input validator** with schema errors surfaced in **<1s** for a bad row.
- **KR3:** Reach **≥70%** unit test coverage on `app/lib/kpis.py`.
- **KR4:** Publish a **4‑minute Loom** walkthrough and link it in the README.

# 💼 JTBD (Jobs-to-be-Done)

**From Alex (Senior PM, SaaS platform):**

- *When I review sprint progress mid-week, I want 3 clear signals, so I can decide if we’re on track without deep-diving.*
- *When I see velocity drop, I want to know the cause (scope churn, staffing, or defects), so I can address the root problem quickly.*

**From Priya (PMO Lead, Enterprise IT):**

- *When I consolidate metrics across 10+ teams, I want consistent definitions, so I can present a trusted roll-up to executives.*
- *When I prepare quarterly reviews, I want defect ratios alongside velocity, so I can show quality and predictability together.*

**From Miguel (Product Owner, Startup AI):**

- *When I run stand-ups, I want to see which stories are slipping, so I can adjust scope before the sprint ends.*
- *When bugs consume half the sprint, I want to visualize the trade-off between features and fixes, so I can defend priorities.*

**From Sarah (Program Manager, Global fintech):**

- *When I track compliance-critical stories, I want early warnings of slippage, so I can escalate before deadlines are missed.*
- *When I share updates with leadership, I want metrics tied to business outcomes, so execs actually pay attention.*

# Launch Checklist

- *Does everyone know what are we launching?*
    - [ ]  **Internal alignment**
        - [x]  Can we explain what this change is?
            
            *Yes. SprintSense is a lightweight Streamlit app that ingests Jira-style CSVs and produces decision-ready sprint KPIs (velocity, throughput, carryover, etc.).*
            
        - [x]  Have you shared details of this change with other functions?
            
            *Yes. The repo, README, and LinkedIn “build-in-public” post already outline scope and progress. This is enough for design, engineering, or leadership peers to understand direction.*
            
    - [ ]  **External messaging**
        - [x]  How are we going to communicate our launch to customers?
            
            Initial comms will be via a LinkedIn post series (weekly build updates). Later, a Medium blog and public Streamlit Cloud deployment link.
            
        - [x]  How will customers understand changes due to this launch?
            
            Clear README instructions + screenshots + a usage demo. Language will emphasize “time saved” and “clarity of metrics.”
            
- *Are we sure this is going to work?*
    - [ ]  **Quality**
        - [x]  Has this change been tested appropriately?
            
            Yes. Pytest pipeline is in place. More unit tests will be added as KPI functions expand.
            
        - [x]  Do we have a contingency plan if the launch doesn’t go well?
            
            Yes. Minimal fallback is CSV validation + simple velocity/throughput charts. Even if advanced metrics fail, the tool still delivers basic value.
            
    - [ ]  **Measurement**
        - [x]  Do we know how to tell if this launch is a success or not?
            
            Yes. Success = sprint health reports in under 5 minutes vs. ~45 minutes manually. Also: clarity feedback from test users (“3 signals that matter” instead of 15 charts).
            
        - [x]  Can others see how this launch is going?
            
            Yes. Progress is documented weekly on GitHub commits and LinkedIn posts. Demo will be public on Streamlit Cloud.
            
- *Question 3: What are our launch steps?*
    - [ ]  **Plan**
        - [x]  Have you agreed on launch audiences with PMM?
            
            Since this is a portfolio project, PMM = myself. Target audiences: recruiters, hiring managers, and peers on LinkedIn.
            
        - [x]  Did we agree on launch steps with PMM?
            
            Yes. Steps are: finish MVP → deploy to Streamlit Cloud → publish write-up/blog → showcase in portfolio.
            

Once MVP is live and stable, the external launch = Streamlit link + Medium blog + LinkedIn announcement.

Checklist (alignment, quality, measurement, launch steps):

- [x]  Internal alignment: Repo structure, tests, schema locked.
- [x]  External messaging: Documenting build-in-public on LinkedIn.
- [x]  Quality: Pytest pipeline running.
- [ ]  Measurement: Will track time saved and reporting clarity.
- [ ]  Launch plan: Streamlit Cloud deploy + portfolio blog.

---
