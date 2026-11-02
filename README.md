# Student Resume Generator (Python Mini Project)

## Overview
A desktop mini project that collects student details through a Tkinter GUI and generates a formatted PDF resume.

## Features
- Tkinter form for personal details, education, skills, projects, experience, and certifications
- Required-field validation
- Basic email and 10-digit phone validation
- Preview the generated PDF in the default PDF viewer before downloading it
- Save-as dialog to choose where the PDF resume is downloaded
- Clear Form button
- Clean, professional resume layout generated with ReportLab

## Requirements
- Python 3.9 or later
- Tkinter (usually included with Python on Windows)
- ReportLab

## How to run
1. Extract the ZIP file.
2. Open Command Prompt or terminal in the project folder.
3. Install the dependency:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the program:
   ```bash
   python main.py
   ```
5. Fill in the required fields and click **Generate Resume PDF**.
6. Review the resume in your default PDF viewer.
7. Return to the app and click **Download PDF**, then choose a location and filename.

## Required fields
Full Name, Email, Phone Number, Course/Degree, College/University, Technical Skills, and Career Objective.

## Project modules
- `main.py`: GUI, validation, and PDF generation
- `requirements.txt`: external Python dependency list

## Possible future improvements
- Add a profile photo
- Add more resume templates
- Save student records to SQLite
- Export a DOCX version
