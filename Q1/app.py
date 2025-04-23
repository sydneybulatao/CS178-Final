from flask import Flask, render_template, request
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from llmproxy import generate

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
  time_options = generate_time_options(5, 10, 15)

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

@app.route('/update', methods=["POST"])
def update():
  request_data = request.get_json()

  filtered_df = df.copy(deep=True)
  filtered_df['date'] = pd.to_datetime(filtered_df['date'], format='%Y-%m-%d %H:%M:%S')

  ### Filter by start and end time
  if 'startTime' in request_data and 'endTime' in request_data:
    start_time_str = request_data['startTime']
    end_time_str = request_data['endTime']

    # Convert to datetime objects
    start_time = datetime.strptime(start_time_str, '%I:%M %p')
    end_time = datetime.strptime(end_time_str, '%I:%M %p')
    start_time = start_time.replace(year=filtered_df['date'].dt.year.iloc[0], month=filtered_df['date'].dt.month.iloc[0], day=filtered_df['date'].dt.day.iloc[0])
    end_time = end_time.replace(year=filtered_df['date'].dt.year.iloc[0], month=filtered_df['date'].dt.month.iloc[0], day=filtered_df['date'].dt.day.iloc[0])

    # Filter dataframe by time range
    filtered_df = filtered_df[(filtered_df['date'] >= start_time) & (filtered_df['date'] <= end_time)]

  ### Filter by time to emergency call
  # Separate 'ccdata' (emergency calls) and 'mbdata' (messages)
  ccdata_df = filtered_df[filtered_df['type'] == 'ccdata']
  mbdata_df = filtered_df[filtered_df['type'] == 'mbdata']

  # Sort to get in ascending order
  ccdata_df = ccdata_df.sort_values(by='date', ascending=True)
  mbdata_df = mbdata_df.sort_values(by='date', ascending=True)

  # Calculate time to most recent emergency call for each mbdata entry 
  mbdata_df['time_to_emergency'] = mbdata_df.apply(
    lambda row: (time_to_most_recent_emergency(ccdata_df, row).total_seconds() / 60) 
    if pd.notnull(time_to_most_recent_emergency(ccdata_df, row)) else np.nan,
    axis=1
)

  if 'emergencyMinutes' in request_data:
    emergency_minutes_start = float(request_data['emergencyMinutes'][0]) 
    emergency_minutes_end = float(request_data['emergencyMinutes'][1])   

    # Filter rows based on whether time_to_emergency is within the specified range
    mbdata_df = mbdata_df[
    (mbdata_df['time_to_emergency'] >= emergency_minutes_start) & 
    (mbdata_df['time_to_emergency'] <= emergency_minutes_end)
    ]

    # Merge the mbdata rows with the time to emergency column back to the filtered_df
    filtered_df = pd.concat([mbdata_df, ccdata_df])

  ### Filter by authors
  if request_data['authors'] and request_data['authors'] != []:
    filtered_df = filtered_df[filtered_df['author'].isin(request_data['authors'])]

  ### Filter by keywords in the message (case-insensitive)
  if request_data['keywords']:
      keyword_pattern = '|'.join([rf'\b{k}\b' for k in request_data['keywords']])
      filtered_df = filtered_df[filtered_df['message'].str.contains(keyword_pattern, case=False, na=False)]

  # Format df for html
  html_df = filtered_df[filtered_df['type'] == 'mbdata'][['author', 'message']].to_html(classes="dataframe", index=False)

  # Generate LLM summary
  summary = generate_summary(filtered_df)
  print("LLM SUMMARY:")
  print(summary)

  return {
    "df": html_df,
    "summary": summary
  }

if __name__ == '__main__':
    app.run(debug=True)
