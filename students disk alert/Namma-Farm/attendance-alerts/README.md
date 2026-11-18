# Student Attendance Risk Alert

A lightweight, high-impact attendance intelligence toolkit for school staff, attendance intervention teams, and administrators. It analyzes weekly attendance records, segments students into actionable risk tiers using excused/unexcused policies, tracks consecutive absences and recent attendance trends, and instantly drafts compassionate, ready-to-send communications to guardians.

---

## Project Structure

```text
/attendance-alerts
  index.html              # Vanilla single-file web application (HTML5/CSS3/JS + Chart.js via CDN)
  attendance_alerts.py    # Python 3 command-line script (standard library only)
  sample_attendance.csv   # Comprehensive sample dataset covering all edge cases
  README.md               # Documentation, rules, and usage guide
```

---

## Attendance & Risk Tier Rules

1. **Overall Attendance Rate**:
   $$\text{Attendance \%} = \frac{\text{days\_present}}{\text{days\_present} + \text{excused} + \text{unexcused}} \times 100$$
   Calculated across all logged weeks. Displayed to guardians and staff to reflect total classroom time.

2. **Risk Tier Calculation (Unexcused Policy)**:
   $$\text{Tier \%} = \frac{\text{days\_present} + \text{excused}}{\text{days\_present} + \text{excused} + \text{unexcused}} \times 100$$
   Intervention tiers are assigned based on **unexcused absences only** by treating excused absences as present for tier classification. Both the Tier % and the Overall Attendance % are displayed side-by-side for full transparency.

3. **Default Risk Tier Thresholds** *(Fully user-adjustable)*:
   - **Critical**: $< 80.0\%$
   - **At risk**: $\ge 80.0\%$ and $< 90.0\%$
   - **Watch**: $\ge 90.0\%$ and $< 95.0\%$
   - **On track**: $\ge 95.0\%$

4. **Consecutive Absence Flag**:
   - Triggers a **`3+ days in a row`** badge on any student with $\ge 3$ consecutive absent days in any single week, regardless of their overall tier. (Threshold adjustable).

5. **Weekly Trend Analysis**:
   - Compares the average attendance of the **last 2 weeks** against the average attendance of **earlier weeks**:
     $$\Delta = \text{Recent Avg (Weeks } n-1, n) - \text{Earlier Avg (Weeks } 1 \dots n-2)$$
   - **Declining**: $\Delta \le -5.0$ percentage points. Triggers a **`Declining`** badge and downward arrow (`↓`), regardless of current tier.
   - **Improving**: $\Delta \ge +2.0$ percentage points (`↑`).
   - **Steady**: Between $-5.0$ and $+2.0$ points (`→`).

6. **Flagged Students**:
   - Any student classified as **Critical**, **At risk**, or **Watch**, OR receiving a **Consecutive Absence** or **Declining** badge.

7. **Guardian Alert Messages**:
   - Warm, supportive, and non-accusatory tone.
   - Formatted with typographic apostrophes (`’` / `\u2019`) throughout.
   - Highlights total days missed with unexcused and excused breakdown, overall attendance percentage, customized tier guidance, specific flag notices, and editable school contact information.

---

## CSV File Format

A valid CSV file requires a header row with the following column names (case-insensitive):

| Column | Type | Required | Description |
|---|---|---|---|
| `name` | String | Yes | Student's full name |
| `week` | Integer | Yes | Week number ($\ge 1$) |
| `days_present` | Integer | Yes | Number of days attended that week ($\ge 0$) |
| `excused` | Integer | Yes | Excused absences that week ($\ge 0$) |
| `unexcused` | Integer | Yes | Unexcused absences that week ($\ge 0$) |
| `consecutive_absent` | Integer | Optional | Longest run of consecutive absent days that week ($\ge 0$, defaults to 0 if omitted) |

*Note: Blank lines and malformed rows (non-integers, missing columns, or impossible zero-day sums) are safely skipped and reported.*

---

## 1. Web Application (`index.html`)

A zero-build, responsive single-file web app built with vanilla HTML, modern CSS, and plain JavaScript, incorporating Chart.js via cdnjs.

### Features
- **Instant CSV Upload & Sample Loader**: Drag and drop your CSV or click "✨ Load Sample Data" for a full live demonstration.
- **Dynamic Risk Summary Tiles**: Real-time student counts and percentages per tier. Click any tile to instantly filter the table.
- **Interactive Visualizations**:
  - Bar chart showing the distribution of students across the 4 risk tiers.
  - Line chart illustrating class-wide attendance trends across each week.
- **Worst-First Ranked Table**:
  - Automatically sorts worst attendance (Critical) to best (On track).
  - Search by student name in real-time.
  - Filter tabs: `All`, `Critical`, `At risk`, `Watch`, `On track`, and `⚠️ Flagged`.
  - Responsive down to 360px viewport width with smooth horizontal table scroll.
- **Guardian Communication Generator**:
  - Click any student to instantly populate a personalized message.
  - Live editable textarea with typographic apostrophes (`’`).
  - One-click "📋 Copy Message" button with animated confirmation feedback.
  - "💾 Save .txt" button to download individual alert messages.
- **Live Threshold Adjustments**:
  - Click "⚙️ Settings & Thresholds" to adjust Critical, At risk, Watch, and Consecutive day thresholds. Recalculates all tiers, charts, and messages in real time.
- **Exporting**:
  - "📥 Download Flagged (CSV)" button exports all flagged students into a structured CSV.
- **Accessibility & Themes**:
  - Automatic light/dark mode via `prefers-color-scheme`, plus a manual toggle (`Auto`, `Light`, `Dark`).
  - High-contrast visual indicators with distinct text badges (not reliant on color alone).
  - Visible keyboard focus styling (`:focus-visible`).

### How to Run the Web App
Simply open `index.html` in any modern web browser:
```bash
# On Windows
start index.html

# Or start a local static server
python -m http.server 8000
# Then visit http://localhost:8000
```

---

## 2. Python Command-Line Tool (`attendance_alerts.py`)

A standalone CLI tool written exclusively with the Python 3 standard library (`csv`, `argparse`, `pathlib`, `sys`).

### Requirements
- Python 3.8+ (No third-party packages or `pip install` required)

### Usage

```bash
# Analyze a CSV file with default thresholds
python attendance_alerts.py sample_attendance.csv

# Customize thresholds and output folder
python attendance_alerts.py sample_attendance.csv --critical 75 --risk 85 --watch 92 --consecutive 2 --out custom_alerts/

# Generate sample_attendance.csv directly
python attendance_alerts.py --sample

# Provide custom school contact details
python attendance_alerts.py sample_attendance.csv --contact "Reach Ms. Vance at 555-0199 or mvance@school.edu."
```

### CLI Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `csv_file` | Path | `sample_attendance.csv` | Path to attendance CSV file |
| `--critical` | Float | `80.0` | Threshold percentage for Critical tier |
| `--risk` | Float | `90.0` | Threshold percentage for At risk tier |
| `--watch` | Float | `95.0` | Threshold percentage for Watch tier |
| `--consecutive` | Integer | `3` | Consecutive absent days badge threshold |
| `--contact` | String | Lincoln High Team | Contact line appended to guardian messages |
| `--out` | String | `alerts` | Directory for `flagged.csv` and alert `.txt` files |
| `--sample` | Flag | `False` | Generates `sample_attendance.csv` and exits |

### Output Files
When executed, the script creates:
1. An ASCII ranked summary table in the terminal and a counts summary line.
2. `alerts/flagged.csv`: A CSV containing all flagged students, their rates, trends, and flags.
3. `alerts/<student_name>_alert.txt`: Individual plain-text alert messages for each flagged student with typographic apostrophes (`’`).

---

## Sample Data Cases Covered

The included `sample_attendance.csv` features 10 students over 6 weeks designed to test every condition:
- **Marcus Vance**: Critical tier (60.0% unexcused rate, steady).
- **Noah Williams**: Critical tier (53.3%), with both a 4-day consecutive streak and a sharp declining trend (-50.0 pts).
- **Sophia Chen**: At risk tier (80.0% unexcused rate, steady).
- **Isabella Kim**: At risk tier (86.7% tier rate vs. 70.0% actual attendance rate due to 5 excused absences). Demonstrates excused absence protection.
- **Olivia Martinez**: Watch tier (90.0% unexcused rate, improving trend +15.0 pts).
- **Liam Rodriguez**: Watch tier (93.3% unexcused rate, steady).
- **Aaliyah Patel**: On track tier (96.7% tier rate), but triggers the **Declining** badge (-20.0 pts drop in weeks 5–6).
- **Jordan Miller**: On track tier (100.0% tier rate), but triggers the **3+ days in a row** badge (3 consecutive excused absences in week 3).
- **Ethan Davis**: On track tier (100.0% tier rate, 96.7% overall, steady/improving).
- **Emma Johnson**: On track tier (100.0% perfect attendance, steady).
