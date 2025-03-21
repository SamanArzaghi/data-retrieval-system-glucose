import os
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import tempfile
import webbrowser
import html
from fpdf import FPDF
from datetime import datetime

def get_available_patient_ids(data_path):
    """Get list of available patient IDs from folder structure."""
    patient_ids = []
    for item in os.listdir(data_path):
        if os.path.isdir(os.path.join(data_path, item)) and item.startswith("CGMacros-"):
            patient_id = item.split("-")[1]
            patient_ids.append(patient_id)
    return sorted(patient_ids)

def get_patient_data(data_path, patient_id):
    """Retrieve data for the specified patient."""
    patient_folder = os.path.join(data_path, f"CGMacros-{patient_id}")
    
    # Assuming there's a CSV file in each patient folder
    for file in os.listdir(patient_folder):
        if file.endswith(".csv"):
            file_path = os.path.join(patient_folder, file)
            return pd.read_csv(file_path)
    
    return None

def prepare_data_summary(data):
    """Prepare a summary of the glucose data for analysis."""
    if data is None:
        return "No data available"
        
    # Calculate basic statistics
    stats = {
        "min_glucose": data["Dexcom GL"].min(),
        "max_glucose": data["Dexcom GL"].max(),
        "avg_glucose": data["Dexcom GL"].mean(),
        "std_glucose": data["Dexcom GL"].std(),
        "data_points": len(data),
        "time_range": f"From {data['Timestamp'].iloc[0]} to {data['Timestamp'].iloc[-1]}"
    }
    
    # Format summary
    summary = f"""
    Time Range: {stats['time_range']}
    Number of readings: {stats['data_points']}
    Minimum glucose: {stats['min_glucose']:.2f} mg/dL
    Maximum glucose: {stats['max_glucose']:.2f} mg/dL
    Average glucose: {stats['avg_glucose']:.2f} mg/dL
    Standard deviation: {stats['std_glucose']:.2f} mg/dL
    """
    
    return summary

def format_raw_data(data, max_rows=15):
    """Format raw data for display."""
    if data is None:
        return "No data available for this patient."
    
    # Return a formatted string of the dataframe
    return data.to_string(max_rows=max_rows) 

def display_raw_data_popup(data, patient_id):
    """Display raw data in a popup window."""
    if data is None:
        return "No data available for this patient."
    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
        # Generate HTML content with styling
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Raw Data for Patient {patient_id}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                }}
                .container {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    padding: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                    overflow-x: auto;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                    position: sticky;
                    top: 0;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .summary {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #e3f2fd;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <h1>Raw Glucose Data for Patient {patient_id}</h1>
            <div class="container">
                <div class="summary">
                    <h3>Data Summary:</h3>
                    <p>Time Range: {data['Timestamp'].iloc[0]} to {data['Timestamp'].iloc[-1]}</p>
                    <p>Number of readings: {len(data)}</p>
                    <p>Min: {data['Dexcom GL'].min():.2f} mg/dL</p>
                    <p>Max: {data['Dexcom GL'].max():.2f} mg/dL</p>
                    <p>Mean: {data['Dexcom GL'].mean():.2f} mg/dL</p>
                    <p>Standard deviation: {data['Dexcom GL'].std():.2f} mg/dL</p>
                </div>
                {data.to_html(index=True)}
            </div>
        </body>
        </html>
        """
        
        f.write(html_content)
        temp_file_path = f.name
    
    # Open the HTML file in the default browser without terminal messages
    try:
        if os.name == 'posix':  # macOS or Linux
            subprocess.Popen(['open', temp_file_path], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        elif os.name == 'nt':  # Windows
            os.startfile(temp_file_path)
        else:
            # Fallback to webbrowser module
            webbrowser.open('file://' + temp_file_path)
    except Exception as e:
        print(f"Could not display the raw data: {e}")
    
    return f"Displaying raw data for patient {patient_id} in your browser."

def generate_glucose_plot(data, patient_id):
    """Generate a plot of glucose levels over time."""
    if data is None:
        return "No data available for this patient."
    
    # Convert timestamp to datetime if it's not already
    try:
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
    except:
        pass  # Already datetime or conversion not possible
    
    # Set a modern style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create figure with better size and DPI for clarity
    fig, ax = plt.subplots(figsize=(14, 8), dpi=100)
    
    # Plot the glucose data with improved styling
    ax.plot(data['Timestamp'], data['Dexcom GL'], 
            linestyle='-', linewidth=2, 
            marker='o', markersize=1, 
            color='#1E88E5', alpha=0.8,
            label='Glucose Level')
    
    # Add reference ranges for normal glucose levels
    ax.axhspan(70, 140, alpha=0.15, color='green', label='Normal Range (70-140 mg/dL)')
    ax.axhline(y=70, linestyle='--', color='orange', alpha=0.7, linewidth=1.5)
    ax.axhline(y=140, linestyle='--', color='orange', alpha=0.7, linewidth=1.5)
    
    # Check for high and low points and annotate them
    max_glucose = data['Dexcom GL'].max()
    min_glucose = data['Dexcom GL'].min()
    max_idx = data['Dexcom GL'].idxmax()
    min_idx = data['Dexcom GL'].idxmin()
    
    ax.plot(data['Timestamp'].iloc[max_idx], max_glucose, 'ro', ms=8, label='Max')
    ax.plot(data['Timestamp'].iloc[min_idx], min_glucose, 'bo', ms=8, label='Min')
    
    # Annotations for max and min
    ax.annotate(f'Max: {max_glucose:.1f}', 
                xy=(data['Timestamp'].iloc[max_idx], max_glucose),
                xytext=(10, 15), textcoords='offset points',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.8))
    
    ax.annotate(f'Min: {min_glucose:.1f}', 
                xy=(data['Timestamp'].iloc[min_idx], min_glucose),
                xytext=(10, -25), textcoords='offset points',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="blue", alpha=0.8))
    
    # Improve title and labels with better formatting
    ax.set_title(f"Glucose Level Monitoring for Patient {patient_id}", 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Time", fontsize=12, labelpad=10)
    ax.set_ylabel("Glucose Level (mg/dL)", fontsize=12, labelpad=10)
    
    # Format x-axis to show readable time
    # This will adapt based on the timespan of the data
    fig.autofmt_xdate()
    
    # Add grid but make it subtle
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # Add legend in a good position
    ax.legend(loc='upper right', frameon=True, framealpha=0.9)
    
    # Add statistics as text on the plot
    stats = f"""
    Mean: {data['Dexcom GL'].mean():.1f} mg/dL
    Std Dev: {data['Dexcom GL'].std():.1f} mg/dL
    Data Points: {len(data)}
    """
    # Place text box in the bottom right of plot
    plt.figtext(0.92, 0.08, stats, horizontalalignment='right',
                bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8))
    
    # Add margins to prevent cutoff
    plt.tight_layout()
    
    # Save plot with higher quality
    plot_path = f"patient_{patient_id}_glucose.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    
    # Open the image without terminal messages
    try:
        if os.name == 'posix':  # macOS or Linux
            subprocess.Popen(['open', plot_path], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        elif os.name == 'nt':  # Windows
            os.startfile(plot_path)
    except Exception as e:
        print(f"Could not display the image: {e}")
    
    return f"Generated enhanced plot for patient {patient_id}. Opening the plot in your default image viewer and saved as {plot_path}" 

def generate_conversation_pdf(conversation_history, patient_id=None):
    """
    Generate a PDF file from the conversation history.
    
    Args:
        conversation_history: List of conversation messages
        patient_id: Optional patient ID to include in the filename
    
    Returns:
        str: Path to the generated PDF file
    """
    if not conversation_history:
        return "No conversation history to export."
    
    # Create a PDF document
    pdf = FPDF()
    pdf.add_page()
    
    # Set up the document
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Glucose Data Assistant - Conversation Log", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(0, 10, f"Generated: {timestamp}", 0, 1, "C")
    
    # Add patient info if available
    if patient_id:
        pdf.cell(0, 10, f"Patient ID: {patient_id}", 0, 1, "C")
    
    pdf.ln(10)
    
    # Add conversation content
    for i, msg in enumerate(conversation_history):
        role = "User" if msg["role"] == "user" else "Bot"
        
        # Set different styles for user and bot
        if role == "User":
            pdf.set_font("Arial", "B", 12)
            pdf.set_text_color(0, 0, 180)  # Dark blue
        else:
            pdf.set_font("Arial", "", 12)
            pdf.set_text_color(0, 0, 0)  # Black
        
        # Add the message with wrapping
        pdf.multi_cell(0, 8, f"{role}: {msg['content']}")
        pdf.ln(5)
    
    # Save the PDF
    filename = f"conversation_log"
    if patient_id:
        filename += f"_patient_{patient_id}"
    filename += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    pdf.output(filename)
    
    # Open the PDF
    try:
        if os.name == 'posix':  # macOS or Linux
            subprocess.Popen(['open', filename], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        elif os.name == 'nt':  # Windows
            os.startfile(filename)
        else:
            # Fallback to webbrowser module
            webbrowser.open('file://' + os.path.abspath(filename))
    except Exception as e:
        print(f"Could not open the PDF: {e}")
    
    return f"Conversation exported to {filename} and opened in your default PDF viewer." 