from flask import Flask, render_template
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

app = Flask(__name__)

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
  # Load in dataset 
  df = pd.read_csv("Data/combined_clean.csv")

  # Generate time options from 5 PM to 10 PM in 15 minute increments
  time_options = generate_time_options(5, 10, 15)

  # Get list of all authors in dataset
  authors = df[df['type'] == 'mbdata']['author'].unique()
  
  return render_template(
    'index.html',
    start_options=time_options,
    end_options=time_options,
    author_options=authors
  )

if __name__ == '__main__':
    app.run(debug=True)
