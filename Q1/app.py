from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from llmproxy import generate
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import seaborn as sns
import re
import io
app = Flask(__name__)
df = pd.read_csv("Data/combined_clean.csv")

def generate_time_options(start_hour, end_hour, increment_minutes):
  """
  Generates a list of time options between start_hour and end_hour, incremented by increment_minutes.
  """
  times = []
  start_time = datetime.strptime(f"{start_hour}:00 PM", "%I:%M %p")
  end_time = datetime.strptime(f"{end_hour}:00 PM", "%I:%M %p")
  
  current_time = start_time
  while current_time <= end_time:
    times.append(current_time.strftime("%I:%M %p"))
    current_time += timedelta(minutes=increment_minutes)

  return times

@app.route('/')
def index():
  # Format df of messages for html
  html_df = df[df['type'] == 'mbdata'][['author', 'message']].to_html(classes="dataframe", index=False)

  # Generate time options from 5 PM to 10 PM in 15 minute increments
  time_options = generate_time_options(5, 10, 1)

  # Get list of all authors in dataset
  authors = sorted(df[df['type'] == 'mbdata']['author'].unique())
  
  return render_template(
    'index.html',
    start_options=time_options,
    end_options=time_options,
    author_options=authors,
    df=html_df
  )

def time_to_most_recent_emergency(ccdata_df, mbdata_row):
  # Find the most recent emergency call before the current 'mbdata' row
  recent_ccdata = ccdata_df[ccdata_df['date'] <= mbdata_row['date']].iloc[-1:]  # Get the most recent one
  if not recent_ccdata.empty:
    # Calculate the time difference (absolute value)
    return mbdata_row['date'] - recent_ccdata['date'].iloc[0]
  return pd.NaT  # If no previous emergency call, return Not a Time

instructions = """
You are an intelligent assistant analyzing a series of posts from a public message board.
Summarize the content of the messages, providing information about the authors and 
messages posted. 

Your task is to:
Write **two sentences** summarizing the content of the messages on the board.

Be objective, concise, and avoid guessing if the data is unclear.

OUTPUT FORMAT:
<2 sentence summary>
"""
def generate_summary(filtered_df):
  # Format messages 
  messages = "\n".join(
    f"{row['author']}: {row['message']}"
    for _, row in filtered_df.iterrows()
  )

  # Send data to LLM to summarize
  response = generate(model = '4o-mini',
    system = instructions,
    query = f"""Summarize the following messages posted on a message board:
                {messages}""",
    temperature = 0.0,
    lastk = 0,
    session_id = "summary_session_cs178-final",
    rag_usage = False)

  return response.get("response", "") if isinstance(response, dict) else response

# this graph is a visual of the density of messages over time
@app.route('/chart-data')
def chart_data():
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d %H:%M:%S')
    df['minute'] = df['date'].dt.floor('min')

    # Group by minute and count messages
    message_counts = df[df['type'] == 'mbdata'].groupby('minute').size()
    data = message_counts.tolist()

    # Normalize heights for colormap
    norm = mcolors.Normalize(vmin=min(data), vmax=max(data))
    cmap = cm.get_cmap('rocket_r') 

    # Generate RGBA hex colors for each bar
    colors = [mcolors.to_hex(cmap(norm(val))) for val in data]

    # Prepare x-axis labels
    labels = [timestamp.strftime('%I:%M %p') for timestamp in message_counts.index]

    return jsonify({
        'labels': labels,
        'data': data,
        'colors': colors
    })


@app.route('/update', methods=["POST"])
def update():
  request_data = request.get_json()

  filtered_df = df.copy(deep=True)
  filtered_df['date'] = pd.to_datetime(filtered_df['date'], format='%Y-%m-%d %H:%M:%S')

  ### Filter by start and end time
  if 'startTime' in request_data and 'endTime' in request_data:
    try:
      start_time_str = request_data['startTime']
      end_time_str = request_data['endTime']

      start_time = datetime.strptime(start_time_str, '%I:%M %p')
      end_time = datetime.strptime(end_time_str, '%I:%M %p')

      sample_date = filtered_df['date'].iloc[0]
      start_time = start_time.replace(year=sample_date.year, month=sample_date.month, day=sample_date.day)
      end_time = end_time.replace(year=sample_date.year, month=sample_date.month, day=sample_date.day)

      filtered_df = filtered_df[(filtered_df['date'] >= start_time) & (filtered_df['date'] <= end_time)]
    except Exception as e:
      print(f"Error parsing time filters: {e}")

  ### Filter by time to emergency call
  if 'emergencyMinutes' in request_data and request_data['emergencyMinutes']:
    try:
      ccdata_df = filtered_df[filtered_df['type'] == 'ccdata'].sort_values(by='date')
      mbdata_df = filtered_df[filtered_df['type'] == 'mbdata'].sort_values(by='date')

      mbdata_df['time_to_emergency'] = mbdata_df.apply(
          lambda row: (time_to_most_recent_emergency(ccdata_df, row).total_seconds() / 60) 
          if pd.notnull(time_to_most_recent_emergency(ccdata_df, row)) else np.nan,
          axis=1
      )

      emergency_minutes_start = float(request_data['emergencyMinutes'][0]) 
      emergency_minutes_end = float(request_data['emergencyMinutes'][1])   

      mbdata_df = mbdata_df[
        (mbdata_df['time_to_emergency'] >= emergency_minutes_start) & 
        (mbdata_df['time_to_emergency'] <= emergency_minutes_end)
      ]

      filtered_df = pd.concat([mbdata_df, ccdata_df])
    except Exception as e:
      print(f"Error applying emergencyMinutes filter: {e}")

  ### Filter by authors
  if 'authors' in request_data and request_data['authors']:
    filtered_df = filtered_df[filtered_df['author'].isin(request_data['authors'])]

  ### Filter by keywords in the message (case-insensitive)
  if 'keywords' in request_data and request_data['keywords']:
    keyword_pattern = '|'.join([rf'\b{k}\b' for k in request_data['keywords']])
    filtered_df = filtered_df[filtered_df['message'].str.contains(keyword_pattern, case=False, na=False)]

  ### Final display and summary
  html_df = filtered_df[filtered_df['type'] == 'mbdata'][['author', 'message']].to_html(classes="dataframe", index=False)

  summary = generate_summary(filtered_df)
  print("LLM SUMMARY:")
  print(summary)

  return {
    "df": html_df,
    "summary": summary
  }

if __name__ == '__main__':
    app.run(debug=True)
