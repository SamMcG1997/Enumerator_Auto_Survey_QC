# Survey Automated Quality Control
#### Video Demo:  <URL HERE>
#### Description:
This project is a web application designed to assist survey supervisors in conducting basic quality control (QC) on survey data in contexts with low capacity or where this type of QC is new. It can be difficult to conduct QC on enumerators as they complete surveys. The goal of this project is to allow an analyst to upload survey data and immediately identify patterns in enumerator performance, helping improve the overall quality of data collection.
The application is built using Python and Flask. Users can upload CSV or Excel files containing survey data, select the relevant columns for analysis, and generate QC metrics including visualizations and summary tables. The system is flexible enough to handle surveys with multiple sections and allows filtering by day to track enumerator performance over time.
The longer-term aim is to expand the application for online hosting so that supervisors anywhere can access it without installing Python locally. Currently, the app functions as a locally hosted tool. Future extensions could include geospatial analysis, ensuring that the enumerators are conducting surveys where expected and a user defined flag for too fast and too slow completion times. 

#### Index.
The index page is the entry point of the application, where users upload survey files. This page ensures that the uploaded file is valid (CSV or Excel) and reads it into a pandas DataFrame. The first five rows of the file are displayed to the user for preview. The uploaded file is temporarily saved as uploads/temp_data.csv for subsequent analysis.
If the file is missing, invalid, or cannot be read, the page displays a flash message notifying the user of the error. Once the file is successfully uploaded, the user is redirected to the Select Columns page, where they choose which columns to use for QC analysis.

#### Select Columns.
The select columns page allows users to specify which columns in the uploaded dataset correspond to enumerator names, survey start times, and survey end times. Users can also define the number of sections in the survey, and for each section, select the relevant start and end columns. This dynamic section selection ensures that the application can handle surveys of varying lengths and structures.
Column selections and section information are stored in Flask sessions so that they can be accessed by the analysis pages without requiring the user to re-upload the file. Any missing or invalid selections trigger a flash message, preventing the user from proceeding with incomplete or incorrect input.

#### Analysis. 
The analysis page is the main output of the application. Here, the uploaded survey data is processed to calculate survey durations for each enumerator and each section. The durations are analysed using the Interquartile Range (IQR) to flag anomalies. Specifically:
-	Too fast: A survey is flagged if its overall or section duration is below Q1 − 1.5 × IQR.
-	Too slow: A survey is flagged if its overall or section duration is above Q3 + 1.5 × IQR.

The page generates visualizations for both overall survey durations and individual sections:
•	Histograms: Display the frequency distribution of survey durations.
•	Empirical Cumulative Distribution Functions (ECDFs): Show the cumulative proportion of surveys completed over time, providing insight into how survey durations are distributed.
Users can filter the analysis by specific days, allowing supervisors to track daily trends. An overall enumerator table summarizes key statistics such as average survey duration, count of surveys, and flags for too fast or too slow responses. Flagged enumerators are highlighted to make it easy for supervisors to identify potential issues.

#### Enumerator Analysis. 
The enumerator analysis page provides a detailed, per-enumerator view. Supervisors can select an enumerator to see all their survey responses. Users can filter this view by specific days using a multiple-selection dropdown. Enumerators are stored as hidden form fields so filtering can occur without losing context. 

#### Stylesheet
The application uses a single CSS file (static/css/style.css) to style all pages. The stylesheet includes:
•	Tables: Styled with borders, padding, and alternating colours for flagged rows. Both overall and section-specific tables are scrollable if necessary.
•	Forms: Styled for usability with dropdowns, buttons, and labels aligned consistently.
•	Flash messages: Displayed in red to catch the user’s attention.
•	Images: Plots are responsive and visually integrated into the interface.
•	Links and headings: Styled for clarity and readability.
The design prioritizes usability and readability, ensuring that supervisors can quickly interpret QC results without unnecessary complexity.

### File Overview:
-	app.py: Main Flask application, handles routes for uploading files, selecting columns, performing analysis, enumerator-specific views, and functions to generate images.
-	templates/: Contains HTML templates (index.html, select_columns.html, analysis.html, enumerator_analysis.html) for each page.
-	static/css/style.css: Styles all pages consistently.
-	uploads/: Temporary storage for user-uploaded survey files and processed CSVs.

