from flask import Flask, render_template, request
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

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
  authors = df[df['type'] == 'mbdata']['author'].unique()
  
  return render_template(
    'index.html',
    start_options=time_options,
    end_options=time_options,
    author_options=authors,
    df=html_df
  )

@app.route('/update', methods=["POST"])
def update():
  request_data = request.get_json()

  # Generate time options from 5 PM to 10 PM in 15 minute increments
  time_options = generate_time_options(5, 10, 15)

  # Get list of all authors in dataset
  authors = df[df['type'] == 'mbdata']['author'].unique()

  # Filter by authors
  filtered_df = df.copy(deep=True)
  if request_data['authors'] and request_data['authors'] != []:
    filtered_df = filtered_df[filtered_df['author'].isin(request_data['authors'])]

  # Filter by keywords in the message (case-insensitive)
  if request_data['keywords']:
      keyword_pattern = '|'.join([rf'\b{k}\b' for k in request_data['keywords']])
      filtered_df = filtered_df[filtered_df['message'].str.contains(keyword_pattern, case=False, na=False)]

  # TODO: filter by start and end time

  # TODO: filter by time to emergency call
  
  print(filtered_df)

  # Format df for html
  html_df = filtered_df[filtered_df['type'] == 'mbdata'][['author', 'message']].to_html(classes="dataframe", index=False)

  return {
    "df": html_df
  }


if __name__ == '__main__':
    app.run(debug=True)
