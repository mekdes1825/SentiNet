# SentiNet — Work Area 5: Security Dashboard & Visualization

A static HTML dashboard displaying SentiNet behavioral detection alerts.

## Status
Currently rendering mock alert data shaped to match area4_detection's
DetectionAlert schema (rule_name, risk_level, score, user_id, reason,
matched_events, timestamp). Next step: connect to a live endpoint
exposing RealTimeMonitor.summary() or BehavioralDetectionEngine.summary()
output.

## Features
- Summary cards (total alerts, critical count, high-risk count, highest risk level)
- Bar chart of alert counts by risk level
- Color-coded alert list (gray/orange/red/dark red by severity)

## Run
Open dashboard.html directly in a browser - no server or dependencies required.
