# Survey Automated Quality Control

## Overview
**Survey Automated Quality Control** is a web application designed to help survey supervisors perform quality control (QC) on survey data, especially in contexts where QC practices are limited or new.  

The tool allows analysts to upload survey datasets and quickly identify patterns in enumerator performance, improving overall data collection quality. Built using Python and Flask, it supports surveys of varying lengths, multiple sections, and daily performance tracking.  

The application currently runs locally, but future online deployment is planned. Potential extensions include geospatial monitoring, user-defined flags for unusually fast or slow surveys, and more advanced analytics.

---

## Features

### 1. File Upload and Validation
- Upload **CSV** or **Excel** survey files.  
- Validate and preview the first 5 rows of the dataset.  
- Temporarily stores uploaded files for analysis (`uploads/temp_data.csv`).  
- Displays clear error messages for invalid or missing files.

### 2. Dynamic Column Selection
- Map dataset columns to **enumerator names**, **survey start times**, and **survey end times**.  
- Supports multiple survey sections with customizable start and end columns.  
- Stores selections in **Flask sessions** for a smooth workflow.  
- Prevents incomplete analysis with validation messages.

### 3. Automated Analysis
- Calculates survey durations per enumerator and per section.  
- Flags anomalies using **Interquartile Range (IQR)**:
  - **Too fast:** duration < Q1 − 1.5 × IQR  
  - **Too slow:** duration > Q3 + 1.5 × IQR  
- Generates visualizations:
  - **Histograms** – survey duration distribution  
  - **ECDFs** – cumulative proportion of surveys over time  
- Filter by specific days to track trends.  
- Summarizes overall statistics in a table with flagged enumerators highlighted.

### 4. Enumerator-Level Insights
- Detailed per-enumerator view with day-based filtering.  
- Enumerator selection persists across filters for easy navigation.

### 5. User Interface and Styling
- **Single CSS file** (`static/css/style.css`) ensures consistent styling:  
  - Tables with alternating colours for flagged rows  
  - Scrollable tables for large datasets  
  - Responsive plots integrated into the interface  
  - Flash messages highlighted for attention  
  - Forms and dropdowns aligned for usability  
- Focused on **clarity and ease of interpretation** for supervisors.

---

## Technologies Used
- **Python** – data processing and QC calculations  
- **Flask** – web framework for routing, session management, and templates  
- **Pandas** – data manipulation  
- **Matplotlib** – visualizations (histograms, ECDFs)  
- **HTML/CSS** – user interface and styling  

---

## Future Enhancements
- Deploy online for remote access  
- Add geospatial verification of enumerator locations  
- Implement user-defined QC thresholds for survey durations  
- Integrate additional analytics dashboards

---

### File Overview:
-	app.py: Main Flask application, handles routes for uploading files, selecting columns, performing analysis, enumerator-specific views, and functions to generate images.
-	templates/: Contains HTML templates (index.html, select_columns.html, analysis.html, enumerator_analysis.html) for each page.
-	static/css/style.css: Styles all pages consistently.
-	uploads/: Temporary storage for user-uploaded survey files and processed CSVs.

