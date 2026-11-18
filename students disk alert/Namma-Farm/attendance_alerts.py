#!/usr/bin/env python3
"""
Student Attendance Risk Alert
A command-line tool to analyze student attendance, identify at-risk students,
and generate ready-to-send messages for guardians.
"""

import sys
import os
import csv
import argparse
import unicodedata
from pathlib import Path

DEFAULT_CRITICAL = 80.0
DEFAULT_RISK = 90.0
DEFAULT_WATCH = 95.0
DEFAULT_CONSECUTIVE = 3
DEFAULT_CONTACT = (
    "Please reach out to our Attendance Support Team at (555) 014-2840 "
    "or attendance@lincolnhigh.edu so we can partner together."
)
DEFAULT_OUT_DIR = "alerts"


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a student name."""
    clean = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    clean = "".join(c if (c.isalnum() or c in ("-", "_")) else "_" for c in clean.strip())
    clean = "_".join(filter(None, clean.split("_")))
    return clean.lower() or "student"


def generate_sample_csv(path: Path) -> None:
    """Generate sample attendance CSV covering all required cases."""
    rows = [
        ("Marcus Vance", 1, 3, 0, 2, 2),
        ("Marcus Vance", 2, 3, 0, 2, 2),
        ("Marcus Vance", 3, 3, 0, 2, 2),
        ("Marcus Vance", 4, 3, 0, 2, 2),
        ("Marcus Vance", 5, 3, 0, 2, 2),
        ("Marcus Vance", 6, 3, 0, 2, 2),
        ("Noah Williams", 1, 4, 0, 1, 1),
        ("Noah Williams", 2, 4, 0, 1, 1),
        ("Noah Williams", 3, 3, 0, 2, 2),
        ("Noah Williams", 4, 3, 0, 2, 2),
        ("Noah Williams", 5, 1, 0, 4, 4),
        ("Noah Williams", 6, 1, 0, 4, 4),
        ("Sophia Chen", 1, 4, 0, 1, 1),
        ("Sophia Chen", 2, 4, 0, 1, 1),
        ("Sophia Chen", 3, 4, 0, 1, 1),
        ("Sophia Chen", 4, 4, 0, 1, 1),
        ("Sophia Chen", 5, 4, 0, 1, 1),
        ("Sophia Chen", 6, 4, 0, 1, 1),
        ("Isabella Kim", 1, 3, 2, 0, 2),
        ("Isabella Kim", 2, 3, 2, 0, 2),
        ("Isabella Kim", 3, 3, 1, 1, 1),
        ("Isabella Kim", 4, 4, 0, 1, 1),
        ("Isabella Kim", 5, 4, 0, 1, 1),
        ("Isabella Kim", 6, 4, 0, 1, 1),
        ("Olivia Martinez", 1, 3, 0, 2, 2),
        ("Olivia Martinez", 2, 4, 0, 1, 1),
        ("Olivia Martinez", 3, 5, 0, 0, 0),
        ("Olivia Martinez", 4, 5, 0, 0, 0),
        ("Olivia Martinez", 5, 5, 0, 0, 0),
        ("Olivia Martinez", 6, 5, 0, 0, 0),
        ("Liam Rodriguez", 1, 4, 1, 0, 1),
        ("Liam Rodriguez", 2, 5, 0, 0, 0),
        ("Liam Rodriguez", 3, 4, 0, 1, 1),
        ("Liam Rodriguez", 4, 5, 0, 0, 0),
        ("Liam Rodriguez", 5, 5, 0, 0, 0),
        ("Liam Rodriguez", 6, 4, 0, 1, 1),
        ("Aaliyah Patel", 1, 5, 0, 0, 0),
        ("Aaliyah Patel", 2, 5, 0, 0, 0),
        ("Aaliyah Patel", 3, 5, 0, 0, 0),
        ("Aaliyah Patel", 4, 5, 0, 0, 0),
        ("Aaliyah Patel", 5, 4, 0, 1, 1),
        ("Aaliyah Patel", 6, 4, 1, 0, 0),
        ("Jordan Miller", 1, 5, 0, 0, 0),
        ("Jordan Miller", 2, 5, 0, 0, 0),
        ("Jordan Miller", 3, 2, 3, 0, 3),
        ("Jordan Miller", 4, 5, 0, 0, 0),
        ("Jordan Miller", 5, 5, 0, 0, 0),
        ("Jordan Miller", 6, 5, 0, 0, 0),
        ("Ethan Davis", 1, 5, 0, 0, 0),
        ("Ethan Davis", 2, 5, 0, 0, 0),
        ("Ethan Davis", 3, 4, 1, 0, 1),
        ("Ethan Davis", 4, 5, 0, 0, 0),
        ("Ethan Davis", 5, 5, 0, 0, 0),
        ("Ethan Davis", 6, 5, 0, 0, 0),
        ("Emma Johnson", 1, 5, 0, 0, 0),
        ("Emma Johnson", 2, 5, 0, 0, 0),
        ("Emma Johnson", 3, 5, 0, 0, 0),
        ("Emma Johnson", 4, 5, 0, 0, 0),
        ("Emma Johnson", 5, 5, 0, 0, 0),
        ("Emma Johnson", 6, 5, 0, 0, 0),
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "week", "days_present", "excused", "unexcused", "consecutive_absent"])
        writer.writerows(rows)


def parse_attendance_csv(file_path: Path):
    """
    Parses attendance CSV file.
    Returns: (records_by_student, skipped_count, error_msg)
    """
    if not file_path.exists():
        return None, 0, f"File not found: '{file_path}'. Please check the file path and try again."

    students = {}
    skipped_count = 0

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = None
            for row in reader:
                if not row or all(c.strip() == "" for c in row):
                    continue
                header = [c.strip().lower() for c in row]
                break

            if not header:
                return None, 0, "The CSV file is empty. Please provide a file with attendance headers and records."

            required_cols = ["name", "week", "days_present", "excused", "unexcused"]
            header_idx = {}
            for col in required_cols:
                try:
                    header_idx[col] = header.index(col)
                except ValueError:
                    return None, 0, (
                        f"Missing required column '{col}'. "
                        f"Required columns: name, week, days_present, excused, unexcused. "
                        f"Found columns: {', '.join(header)}."
                    )

            consecutive_idx = header.index("consecutive_absent") if "consecutive_absent" in header else None

            for row_num, row in enumerate(reader, start=2):
                if not row or all(c.strip() == "" for c in row):
                    skipped_count += 1
                    continue

                if len(row) <= max(header_idx.values()):
                    skipped_count += 1
                    continue

                name = row[header_idx["name"]].strip()
                if not name:
                    skipped_count += 1
                    continue

                try:
                    week = int(row[header_idx["week"]].strip())
                    days_present = int(row[header_idx["days_present"]].strip())
                    excused = int(row[header_idx["excused"]].strip())
                    unexcused = int(row[header_idx["unexcused"]].strip())

                    consec = 0
                    if consecutive_idx is not None and consecutive_idx < len(row):
                        raw_c = row[consecutive_idx].strip()
                        if raw_c:
                            consec = int(raw_c)

                    if week < 0 or days_present < 0 or excused < 0 or unexcused < 0 or consec < 0:
                        skipped_count += 1
                        continue

                    total_days = days_present + excused + unexcused
                    if total_days <= 0:
                        skipped_count += 1
                        continue

                except ValueError:
                    skipped_count += 1
                    continue

                if name not in students:
                    students[name] = []

                students[name].append({
                    "week": week,
                    "days_present": days_present,
                    "excused": excused,
                    "unexcused": unexcused,
                    "consecutive_absent": consec,
                    "total_days": total_days,
                })

    except Exception as e:
        return None, 0, f"Error reading CSV file: {str(e)}"

    if not students:
        return None, skipped_count, "No valid student attendance records found in the CSV file."

    return students, skipped_count, None


def analyze_student(name: str, weekly_records: list, thresholds: dict) -> dict:
    """Analyze a single student's attendance records."""
    records_sorted = sorted(weekly_records, key=lambda r: r["week"])

    total_present = sum(r["days_present"] for r in records_sorted)
    total_excused = sum(r["excused"] for r in records_sorted)
    total_unexcused = sum(r["unexcused"] for r in records_sorted)
    total_enrolled = total_present + total_excused + total_unexcused
    total_missed = total_excused + total_unexcused

    # Attendance %: days_present / total_enrolled * 100
    overall_pct = (total_present / total_enrolled * 100.0) if total_enrolled > 0 else 0.0

    # Tiers use UNEXCUSED absences only: treat excused as present
    tier_pct = ((total_present + total_excused) / total_enrolled * 100.0) if total_enrolled > 0 else 0.0

    # Determine Tier
    crit_th = thresholds["critical"]
    risk_th = thresholds["risk"]
    watch_th = thresholds["watch"]

    if tier_pct < crit_th:
        tier = "Critical"
        tier_rank = 1
    elif tier_pct < risk_th:
        tier = "At risk"
        tier_rank = 2
    elif tier_pct < watch_th:
        tier = "Watch"
        tier_rank = 3
    else:
        tier = "On track"
        tier_rank = 4

    # Max consecutive absent
    max_consecutive = max(r["consecutive_absent"] for r in records_sorted)
    consecutive_flag = max_consecutive >= thresholds["consecutive"]

    # Weekly trend: compare average of last 2 weeks to average of earlier weeks
    weekly_pcts = [
        (r["days_present"] / r["total_days"] * 100.0) if r["total_days"] > 0 else 0.0
        for r in records_sorted
    ]

    n_weeks = len(weekly_pcts)
    if n_weeks >= 3:
        recent_avg = sum(weekly_pcts[-2:]) / 2.0
        earlier_avg = sum(weekly_pcts[:-2]) / float(n_weeks - 2)
        trend_diff = recent_avg - earlier_avg

        if trend_diff <= -5.0:
            trend = "Declining"
            trend_arrow = "↓"
            declining_flag = True
        elif trend_diff >= 2.0:
            trend = "Improving"
            trend_arrow = "↑"
            declining_flag = False
        else:
            trend = "Steady"
            trend_arrow = "→"
            declining_flag = False
    else:
        trend = "Steady"
        trend_arrow = "→"
        trend_diff = 0.0
        declining_flag = False

    is_flagged = (tier in ("Critical", "At risk", "Watch")) or consecutive_flag or declining_flag

    badges = []
    if consecutive_flag:
        badges.append(f"{thresholds['consecutive']}+ days in a row")
    if declining_flag:
        badges.append("Declining")

    return {
        "name": name,
        "total_present": total_present,
        "total_excused": total_excused,
        "total_unexcused": total_unexcused,
        "total_missed": total_missed,
        "total_enrolled": total_enrolled,
        "overall_pct": round(overall_pct, 1),
        "tier_pct": round(tier_pct, 1),
        "tier": tier,
        "tier_rank": tier_rank,
        "max_consecutive": max_consecutive,
        "consecutive_flag": consecutive_flag,
        "declining_flag": declining_flag,
        "trend": trend,
        "trend_arrow": trend_arrow,
        "trend_diff": round(trend_diff, 1),
        "is_flagged": is_flagged,
        "badges": badges,
        "weekly_records": records_sorted,
    }


def generate_alert_message(student: dict, contact_line: str) -> str:
    """
    Generates warm, supportive, non-accusatory alert message matching web app exactly.
    Uses typographic apostrophes (’ / \\u2019).
    """
    name = student["name"]
    tier = student["tier"]
    missed = student["total_missed"]
    excused = student["total_excused"]
    unexcused = student["total_unexcused"]
    overall_pct = f"{student['overall_pct']:.1f}%"
    max_c = student["max_consecutive"]

    # Days missed text with breakdown
    if missed == 0:
        missed_str = "no school days (0 unexcused, 0 excused)"
    elif missed == 1:
        missed_str = f"1 day of school ({unexcused} unexcused, {excused} excused)"
    else:
        missed_str = f"{missed} days of school ({unexcused} unexcused, {excused} excused)"

    # Flag notices
    flag_paragraphs = []
    if student["consecutive_flag"]:
        flag_paragraphs.append(
            f"We also noticed a recent streak of {max_c} consecutive days away from class, "
            f"and we wanted to check in to make sure everything is okay and that {name} feels supported in getting caught up."
        )

    if student["declining_flag"]:
        flag_paragraphs.append(
            f"Additionally, {name}’s attendance has dipped over the past two weeks compared to earlier in the term, "
            f"and we’d love to work together to turn that trend around before it creates learning hurdles."
        )

    # Tier-specific body text
    if tier == "Critical":
        tier_body = (
            f"Because missing this amount of classroom time places {name} at critical academic risk, "
            f"we would like to schedule a brief meeting or phone conversation this week. "
            f"Our goal is to understand any obstacles your family may be facing and build a positive, realistic plan forward."
        )
    elif tier == "At risk":
        tier_body = (
            f"We are reaching out early because consistent attendance is closely linked with feeling confident and connected in school. "
            f"These absences are beginning to place {name} at risk of falling behind, and we want to partner with you to help ensure regular attendance."
        )
    elif tier == "Watch":
        tier_body = (
            f"We are sharing this gentle update so we can stay ahead of any emerging patterns together. "
            f"Keeping attendance strong now helps {name} stay engaged, comfortable, and on track with daily learning."
        )
    else:  # On track with flag
        tier_body = (
            f"While {name}’s cumulative attendance remains strong overall, "
            f"we wanted to share the specific observation noted above so we can keep communication open and support your family."
        )

    flags_text = "\n\n".join(flag_paragraphs)
    if flags_text:
        flags_text = f"\n\n{flags_text}"

    message = (
        f"Dear Family of {name},\n\n"
        f"We’re reaching out from school to partner with you regarding {name}’s attendance. "
        f"Every day in the classroom brings valuable moments for learning, connection, and growth.\n\n"
        f"So far this term, {name} has missed {missed_str}, and their overall attendance rate is currently {overall_pct}.{flags_text}\n\n"
        f"{tier_body}\n\n"
        f"{contact_line}\n\n"
        f"Thank you for your ongoing care and partnership in {name}’s education.\n\n"
        f"Warmly,\n"
        f"Student Attendance Support Team"
    )

    return message


def write_outputs(students_analyzed: list, out_dir: Path, contact_line: str):
    """Write flagged.csv and individual student alert .txt files."""
    out_dir.mkdir(parents=True, exist_ok=True)

    flagged_students = [s for s in students_analyzed if s["is_flagged"]]

    # Write flagged.csv
    flagged_csv_path = out_dir / "flagged.csv"
    with open(flagged_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "name",
            "tier",
            "tier_pct",
            "overall_pct",
            "days_present",
            "excused",
            "unexcused",
            "total_missed",
            "consecutive_absent_max",
            "trend",
            "flags"
        ])
        for s in flagged_students:
            writer.writerow([
                s["name"],
                s["tier"],
                f"{s['tier_pct']:.1f}",
                f"{s['overall_pct']:.1f}",
                s["total_present"],
                s["total_excused"],
                s["total_unexcused"],
                s["total_missed"],
                s["max_consecutive"],
                s["trend"],
                "; ".join(s["badges"]) if s["badges"] else "None",
            ])

    # Write individual alert messages
    for s in flagged_students:
        slug = sanitize_filename(s["name"])
        alert_file = out_dir / f"{slug}_alert.txt"
        content = generate_alert_message(s, contact_line)
        with open(alert_file, "w", encoding="utf-8") as f:
            f.write(content)

    return len(flagged_students), flagged_csv_path


def format_table(students: list) -> str:
    """Format an ASCII table ranking students from worst attendance to best."""
    sorted_students = sorted(students, key=lambda s: (s["tier_rank"], s["tier_pct"], s["overall_pct"]))

    headers = ["Rank", "Student Name", "Tier", "Tier %", "Overall %", "Missed (Un/Ex)", "Consec.", "Trend", "Badges"]
    rows = []

    for idx, s in enumerate(sorted_students, start=1):
        tier_str = s["tier"]
        tier_pct_str = f"{s['tier_pct']:.1f}%"
        overall_str = f"{s['overall_pct']:.1f}%"
        missed_str = f"{s['total_missed']} ({s['total_unexcused']}u/{s['total_excused']}e)"
        consec_str = str(s["max_consecutive"])
        trend_str = f"{s['trend_arrow']} {s['trend']}"
        badges_str = ", ".join(s["badges"]) if s["badges"] else "-"

        rows.append([
            str(idx),
            s["name"],
            tier_str,
            tier_pct_str,
            overall_str,
            missed_str,
            consec_str,
            trend_str,
            badges_str,
        ])

    col_widths = [len(h) for h in headers]
    for r in rows:
        for i, val in enumerate(r):
            if len(val) > col_widths[i]:
                col_widths[i] = len(val)

    def make_row(vals):
        return " | ".join(v.ljust(col_widths[i]) for i, v in enumerate(vals))

    separator = "-+-".join("-" * w for w in col_widths)

    table_lines = [
        make_row(headers),
        separator,
    ]
    for r in rows:
        table_lines.append(make_row(r))

    return "\n".join(table_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Student Attendance Risk Alert: identify students needing support and generate guardian alerts."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default=None,
        help="Path to attendance CSV file."
    )
    parser.add_argument(
        "--critical",
        type=float,
        default=DEFAULT_CRITICAL,
        help=f"Threshold percentage for Critical tier (default: {DEFAULT_CRITICAL})"
    )
    parser.add_argument(
        "--risk",
        type=float,
        default=DEFAULT_RISK,
        help=f"Threshold percentage for At risk tier (default: {DEFAULT_RISK})"
    )
    parser.add_argument(
        "--watch",
        type=float,
        default=DEFAULT_WATCH,
        help=f"Threshold percentage for Watch tier (default: {DEFAULT_WATCH})"
    )
    parser.add_argument(
        "--consecutive",
        type=int,
        default=DEFAULT_CONSECUTIVE,
        help=f"Consecutive absent days badge threshold (default: {DEFAULT_CONSECUTIVE})"
    )
    parser.add_argument(
        "--contact",
        type=str,
        default=DEFAULT_CONTACT,
        help="Custom contact line included at the end of guardian alert messages."
    )
    parser.add_argument(
        "--out",
        type=str,
        default=DEFAULT_OUT_DIR,
        help=f"Output directory for flagged.csv and guardian alert .txt files (default: {DEFAULT_OUT_DIR})"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Generate sample_attendance.csv in the current working directory and exit."
    )

    args = parser.parse_args()

    # Handle --sample
    if args.sample:
        target_sample = Path("sample_attendance.csv")
        generate_sample_csv(target_sample)
        print(f"Sample attendance data successfully written to: {target_sample.resolve()}")
        if not args.csv_file:
            return 0

    if not args.csv_file:
        if Path("sample_attendance.csv").exists():
            csv_path = Path("sample_attendance.csv")
            print(f"No CSV file specified. Using existing: {csv_path.resolve()}\n")
        else:
            parser.print_help()
            print("\nError: Please provide a path to a CSV file or use --sample to generate one.")
            return 1
    else:
        csv_path = Path(args.csv_file)

    thresholds = {
        "critical": args.critical,
        "risk": args.risk,
        "watch": args.watch,
        "consecutive": args.consecutive,
    }

    if not (args.critical < args.risk < args.watch):
        print(
            f"Error: Invalid thresholds! Expected: critical < risk < watch "
            f"(got: critical={args.critical}, risk={args.risk}, watch={args.watch})."
        )
        return 1

    records_by_student, skipped_count, err = parse_attendance_csv(csv_path)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    if skipped_count > 0:
        print(f"Notice: Skipped {skipped_count} blank or malformed row(s) in {csv_path.name}.")

    students_analyzed = []
    for name, records in records_by_student.items():
        analyzed = analyze_student(name, records, thresholds)
        students_analyzed.append(analyzed)

    students_analyzed.sort(key=lambda s: (s["tier_rank"], s["tier_pct"], s["overall_pct"]))

    tier_counts = {"Critical": 0, "At risk": 0, "Watch": 0, "On track": 0}
    for s in students_analyzed:
        tier_counts[s["tier"]] += 1

    flagged_count = sum(1 for s in students_analyzed if s["is_flagged"])

    print("\n" + "=" * 80)
    print(" STUDENT ATTENDANCE RISK RANKINGS (Worst Attendance First)")
    print("=" * 80)
    print(format_table(students_analyzed))
    print("-" * 80)

    print(
        f"Summary: {tier_counts['Critical']} Critical, {tier_counts['At risk']} At risk, "
        f"{tier_counts['Watch']} Watch, {tier_counts['On track']} On track "
        f"({flagged_count} Flagged total across {len(students_analyzed)} students)"
    )
    print("=" * 80)

    out_dir = Path(args.out)
    num_written, flagged_csv_path = write_outputs(students_analyzed, out_dir, args.contact)
    print(f"\nExport complete in '{out_dir}/':")
    print(f"  • Flagged students list: {flagged_csv_path.name} ({num_written} students)")
    print(f"  • Alert message files:   {num_written} text file(s) generated.")
    print("  Done!\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
