# SentiNet — Area 1: Phishing Simulation & Human Risk

## Overview

Area 1 focuses on simulating phishing attacks in a controlled environment to demonstrate how human behavior can contribute to cybersecurity risks.

The module provides simulated phishing messages, a mock login interaction, and an educational page to help users recognize phishing attempts. It is designed to integrate with SentiNet's shared event logging and detection components.

**Important:** This is a security-awareness simulation. It must not collect or store real user passwords or use real banking credentials.

## Features

- **Phishing campaign interface:** Provides an interface for managing or initiating phishing simulations.
- **Simulated phishing message:** Presents a mock phishing message for the target user.
- **Mock login page:** Demonstrates a phishing-style login interaction without requiring real account credentials.
- **Learning page:** Helps users understand phishing risks and identify suspicious messages.
- **Event logging:** Integrates with SentiNet's shared event-logging module.
- **Human risk integration:** Imports the shared human-risk functionality to support risk assessment.

## Project Structure

```text
area1_phishing/
├── phishing.py
└── templates/
    ├── phish_admin.html
    ├── phish_msg.html
    ├── phish_login.html
    └── phish_learn.html
```

## Dependencies and Integration

The module imports shared components from the main SentiNet application:

- `db.py` — database queries and execution.
- `detection.py` — human-risk and detection functionality.
- `events.py` — security-event logging.

The shared application must provide the expected database tables, fields, and functions before the module can operate correctly.

The module also uses Flask functionality for routing, templates, requests, and redirects.

## Setup

1. Clone the SentiNet repository.
2. Open the repository in your terminal or IDE.
3. Create and activate a Python virtual environment.
4. Install the project's required Python packages.
5. Ensure the shared database, detection, and event-logging components are configured.
6. Register the `phish` Blueprint with the main Flask application.
7. Configure the required database tables and campaign data before testing the simulation.

**Current implementation status:** The Area 1 source files have been added to the feature branch. The module's compatibility with the shared application must be verified before it can be considered runnable. This folder does not currently include the standalone `app.py` and `database.py` files from the previous implementation.

## Safety Notes

- Use only authorized test users and controlled simulations.
- Never request or store real passwords.
- Do not send simulated phishing messages to people without appropriate authorization.
- Keep simulation events limited to the information needed for security-awareness testing.

## Development Status

Area 1 contains the replacement phishing-simulation implementation and its HTML templates. Integration testing is still required to verify its routes, database operations, event logging, and human-risk calculations within the complete SentiNet application.
