import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import uuid
import numpy as np

app = Flask(__name__)
app.secret_key = "dev"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


#Upload file
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in request.")
            return redirect(request.url)

        file = request.files["file"]

        # Validate file name
        if file.filename == "":
            flash("No file selected.")
            return redirect(request.url)

        # Check allowed file types
        if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
            flash("Please upload a CSV or XLSX file.")
            return redirect(request.url)

        # Save the file
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        # Read with pandas
        try:
            if file.filename.endswith(".csv"):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
        except Exception as e:
            flash(f"Error reading file: {e}")
            return redirect(request.url)

        # Store the columns temporarily
        columns = df.columns.tolist()
        df.to_csv("uploads/temp_data.csv", index=False)  # keep for next step

        # Redirect to column selection
        return render_template("select_columns.html", columns=columns)

    return render_template("index.html")


#Select columns
@app.route("/select_columns", methods=["POST"])
def select_columns():
    sections = request.form.get("sections")
    try:
        sections = int(sections)
    except ValueError:
        flash("Invalid number of sections.")
        return redirect(url_for("index"))

    enumerator_col = request.form.get("enumerator_col")
    start_col = request.form.get("start_col")
    end_col = request.form.get("end_col")

    section_cols = {}

    for i in range(1, sections+1):
        section_start_col = request.form.get(f"section_{i}_start")
        section_end_col = request.form.get(f"section_{i}_end")
        section_cols[i] = {"start": section_start_col, "end": section_end_col}

    if not enumerator_col or not start_col or not end_col:
        flash("Please select all columns.")
        return redirect(url_for("index"))

    if enumerator_col in [start_col, end_col]:
        flash("Enumerator and time columns cannot be the same.")
        return redirect(url_for("index"))
    
    if start_col == end_col:
        flash("Main start and end times must be different.")
        return redirect(url_for("index"))
    
    session["sections"] = sections
    session["section_cols"] = section_cols
    session["start_col"] = start_col
    session["end_col"] = end_col
    session["enumerator_col"] = enumerator_col

    # Next stage will process data here.
    return redirect(url_for("analysis"))


#Analysis
@app.route("/analysis", methods=["GET", "POST"])
def analysis():

    df = pd.read_csv("uploads/temp_data.csv")
    qc_table = {}
    hist_paths = []
    ecdf_paths = []
    unique_enums = []

    # Load session data
    enumerator_col = session.get("enumerator_col")
    start_col = session.get("start_col")
    end_col = session.get("end_col")
    sections = int(session.get("sections"))
    section_cols = session.get("section_cols")

    # Convert main start/end columns to datetime
    df[start_col] = pd.to_datetime(df[start_col], errors="coerce")
    df[end_col] = pd.to_datetime(df[end_col], errors="coerce")
    df["time_col"] = (df[end_col] - df[start_col]).dt.total_seconds() / 60
    Q1 = df["time_col"].quantile(0.25)
    Q3 = df["time_col"].quantile(0.75)
    IQR = Q3 - Q1

    df[f"too_fast"] = df["time_col"] < (Q1 - 1.5 * IQR)
    df[f"too_slow"] = df["time_col"] > (Q3 + 1.5 * IQR)

    os.makedirs("static", exist_ok=True)
    hist_filename = "overall_hist.png"
    ecdf_filename = "overall_ecdf.png"

    hist_plot(df["time_col"], hist_filename)
    ecdf_plot(df["time_col"], ecdf_filename)

    overall_hist = hist_filename
    overall_ecdf = ecdf_filename

    # Unique enumerators
    unique_enums = sorted(df[enumerator_col].dropna().unique())

    enumerator_avg = df.groupby(enumerator_col)["time_col"].mean()
    count_per_enum = df.groupby(enumerator_col)["time_col"].count()
    fast_per_enum = df.groupby(enumerator_col)["too_fast"].sum()
    slow_per_enum = df.groupby(enumerator_col)["too_slow"].sum()

            # Build QC table
    for name in enumerator_avg.index:
        if name not in qc_table:
            qc_table[name] = {}

        qc_table[name]["avg_time"] = round(enumerator_avg[name], 2)
        qc_table[name]["count"] = int(count_per_enum[name])
        qc_table[name]["too_fast"] = int(fast_per_enum[name])
        qc_table[name]["too_slow"] = int(slow_per_enum[name])
        qc_table[name]["flagged"] = fast_per_enum[name] > 0 or slow_per_enum[name] > 0

        # Loop through each section
    for i in range(1, sections + 1):
        sec_start = section_cols[str(i)]["start"]
        sec_end = section_cols[str(i)]["end"]

        df[sec_start] = pd.to_datetime(df[sec_start], errors="coerce")
        df[sec_end] = pd.to_datetime(df[sec_end], errors="coerce")

        # Compute section duration in minutes
        df[f"section_{i}_time_col"] = (df[sec_end] - df[sec_start]).dt.total_seconds() / 60

        # QC calculations
        Q1 = df[f"section_{i}_time_col"].quantile(0.25)
        Q3 = df[f"section_{i}_time_col"].quantile(0.75)
        IQR = Q3 - Q1

        df[f"section_{i}_too_fast"] = df[f"section_{i}_time_col"] < (Q1 - 1.5 * IQR)
        df[f"section_{i}_too_slow"] = df[f"section_{i}_time_col"] > (Q3 + 1.5 * IQR)

        # Aggregation per enumerator
        enumerator_avg = df.groupby(enumerator_col)[f"section_{i}_time_col"].mean()
        count_per_enum = df.groupby(enumerator_col)[f"section_{i}_time_col"].count()
        fast_per_enum = df.groupby(enumerator_col)[f"section_{i}_too_fast"].sum()
        slow_per_enum = df.groupby(enumerator_col)[f"section_{i}_too_slow"].sum()

        # Build QC table
        for name in enumerator_avg.index:
            if name not in qc_table:
                qc_table[name] = {}

            qc_table[name][f"section_{i}_avg_time"] = round(enumerator_avg[name], 2)
            qc_table[name][f"section_{i}_count"] = int(count_per_enum[name])
            qc_table[name][f"section_{i}_too_fast"] = int(fast_per_enum[name])
            qc_table[name][f"section_{i}_too_slow"] = int(slow_per_enum[name])
            qc_table[name][f"section_{i}_flagged"] = fast_per_enum[name] > 0 or slow_per_enum[name] > 0

        # Generate plots
        hist_filename = f"section_{i}_hist.png"
        ecdf_filename = f"section_{i}_ecdf.png"

        hist_plot(df[f"section_{i}_time_col"], hist_filename)
        ecdf_plot(df[f"section_{i}_time_col"], ecdf_filename)

        hist_paths.append(hist_filename)
        ecdf_paths.append(ecdf_filename)
    
    return render_template(
        "analysis.html",
        qc_table=qc_table,
        overall_hist = overall_hist,
        overall_ecdf = overall_ecdf,
        hist_paths=hist_paths,
        ecdf_paths=ecdf_paths,
        unique_enums=unique_enums
    )
    


@app.route("/enumerator_analysis", methods=["POST"])
def enumerator_analysis():
    enum_name = request.form.get("enum_name")

    # Load dataset again
    df = pd.read_csv("uploads/temp_data.csv")

    # Retrieve the stored column names
    enumerator_col = session.get("enumerator_col")
    start_col = session.get("start_col")
    end_col = session.get("end_col")

    if not all([enumerator_col, start_col, end_col]):
        flash("Error: Missing analysis settings. Please re-upload your file.")
        return redirect(url_for("index"))

    # Filter data for this enumerator
    df_enum = df[df[enumerator_col] == enum_name]

    if df_enum.empty:
        flash(f"No data found for enumerator: {enum_name}")
        return redirect(url_for("analysis"))

    # Create unique filename
    enum_filename = "enum_hist.png"

    df_enum[end_col] = pd.to_datetime(df_enum[end_col], errors="coerce")
    df_enum[start_col] = pd.to_datetime(df_enum[start_col], errors="coerce")
    df_enum["time_col"] = round((df_enum[end_col] - df_enum[start_col]).dt.total_seconds()/60)
    df_enum = df_enum.dropna(subset=["time_col"])

    Q1 = df_enum["time_col"].quantile(0.25)
    Q3 = df_enum["time_col"].quantile(0.75)
    IQR = Q3 - Q1
    df_enum["too_fast"] = (df_enum["time_col"] < Q1 - 1.5*IQR)
    df_enum["too_slow"] = (df_enum["time_col"] > Q3 + 1.5*IQR)

    hist_plot(df_enum["time_col"], enum_filename, freedman_diaconis=0)

    enum_data = df_enum.to_dict(orient="records")

    return render_template(
        "enumerator_analysis.html",
        enum_name=enum_name,
        hist_filename=enum_filename,
        enum_data=enum_data
    )


#Helper Functons
def ecdf_plot(values, filename):
    no_nans = values[~np.isnan(values)]
    x = np.sort(no_nans)
    y = np.arange(1, len(no_nans) + 1) / len(no_nans)

    plt.figure(figsize=(8,5))
    plt.plot(x,y)
    plt.xlabel("Duration (Minutes)")
    plt.ylabel("Empirical Cumulative Distribution Function")
    plt.title("Distribution of Surveys")
    plt.grid(True)
    plt.savefig(os.path.join("static",filename))
    plt.close()


def hist_plot(values, filename, freedman_diaconis=1):
    no_nans = values[~np.isnan(values)]
    if freedman_diaconis != 1:
        plt.figure(figsize=(8, 5))
        plt.hist(no_nans, bins=10, edgecolor='black')
        plt.xlabel('Duration (Minutes)')
        plt.ylabel('Frequency')
        plt.title('Histogram of Durations')
        plt.savefig(os.path.join("static",filename))
        plt.close()

    else:
        #Freedman-Diaconis Rule for Histo Bins
        q25, q75 = np.percentile(no_nans, [25, 75])
        iqr = q75 - q25
        bin_width = (2 * iqr * len(no_nans) ** (-1/3))
        bins = int(np.ceil((no_nans.max() - no_nans.min()) / bin_width))

        plt.figure(figsize=(8, 5))
        plt.hist(no_nans, bins=bins, edgecolor='black')
        plt.xlabel('Duration (Minutes)')
        plt.ylabel('Frequency')
        plt.title('Histogram of Durations')
        plt.savefig(os.path.join("static",filename))
        plt.close()

if __name__ == "__main__":
    app.run(debug=True)

