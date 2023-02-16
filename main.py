import os
from typing import Union
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

import models

import api

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello", "World"}

samples = api.samples_from_csv(filepath=os.path.join("tests","glucose_real_data.csv"))
stats = models.Stats.from_sample_collection(samples)

@app.get("/samples")
def read_samples(day: Union[str, None] = None):
    if day is None:
        return list(filter(lambda d: d.sampling_date.date() == datetime.today().date(), samples))
    return list(filter(lambda d: datetime.strptime(day, "%d-%m-%Y").date() == d.sampling_date.date(), samples))

@app.get("/stats")
def read_stats():
    return stats

@app.get("/trend/hours_interval")
def read_trend_hours(h1_string: str, h2_string: str, error: int):
    h1 = datetime.strptime(h1_string, "%d-%m-%Y_%H:%M")
    h2 = datetime.strptime(h2_string, "%d-%m-%Y_%H:%M")
    return models.HourTrend.from_hours(h1,h2,samples, error)

@app.get("/trend/days_interval")
def read_trend_days(day1_string: str, day2_string: str, error: int):
    day1 = datetime.strptime(day1_string, "%d-%m-%Y")
    day2 = datetime.strptime(day2_string, "%d-%m-%Y")
    return models.HourTrend.from_hours(day1,day2,samples, error)

@app.get("/trend/months_interval")
def read_trend_months(month1: int, year1: int, month2: int, year2: int, error: int):
    return models.MonthTrend.from_months(month1, year1, month2, year2, samples, error)