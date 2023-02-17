import os
from typing import Optional, Union
from datetime import datetime

import json

from fastapi import FastAPI

import models

import api

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello", "World"}

samples = {data.split('_')[0]+"_"+data.split('_')[1]: api.samples_from_csv(filepath=os.path.join("users_data", f"{data}")) for data in os.listdir("users_data")}

stats = {key: models.Stats.from_sample_collection(samples[key]) for key in samples}

@app.get("/user/{username}/samples")
def read_samples(username: str, day: Optional[str] = None):
    if day is None:
        return list(filter(lambda d: d.sampling_date.date() == datetime.today().date(), samples))
    return list(filter(lambda d: datetime.strptime(day, "%d-%m-%Y").date() == d.sampling_date.date(), samples[username]))

@app.get("/user/{username}/stats")
def read_stats(username: str):
    return stats[username]

@app.get("/trend/{username}/hours_interval")
def read_trend_hours(username: str, h1_string: str, h2_string: str, error: int):
    h1 = datetime.strptime(h1_string, "%d-%m-%Y_%H:%M")
    h2 = datetime.strptime(h2_string, "%d-%m-%Y_%H:%M")
    return models.HourTrend.from_hours(h1,h2,samples[username], error)

@app.get("/trend/{username}/days_interval")
def read_trend_days(username: str, day1_string: str, day2_string: str, error: int):
    day1 = datetime.strptime(day1_string, "%d-%m-%Y")
    day2 = datetime.strptime(day2_string, "%d-%m-%Y")
    return models.HourTrend.from_hours(day1,day2,samples[username], error)

@app.get("/trend/{username}/months_interval")
def read_trend_months(username: str, month1: int, year1: int, month2: int, year2: int, error: int):
    return models.MonthTrend.from_months(month1, year1, month2, year2, samples[username], error)