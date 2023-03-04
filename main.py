import os
from typing import Optional, Union
from datetime import datetime

import json

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse

import models

import api

app = FastAPI()

# Storing available data in variables
samples = {data.split('_')[0]+"_"+data.split('_')[1]: api.samples_from_csv(filepath=os.path.join("users_data", f"{data}")) for data in os.listdir("users_data")}
stats = {key: models.Stats.from_sample_collection(samples[key]) for key in samples}

@app.get("/")
async def read_root():
    f = open("pages/index.html", "r")
    content = f.read()
    f.close()
    return HTMLResponse(content=content)

@app.post("/file_uploaded.html")
async def upload_csv_data(personal_data: UploadFile, firstname: str = Form(), lastname: str = Form()):
    try:
        f = open("pages/file_uploaded.html", "r")
        content = f.read().replace("[[content]]", personal_data.filename)
        f.close()
        today_str = datetime.today().strftime("%d-%m-%Y")
        # Creating the CSV file for data storing
        f_data = open(os.path.join("users_data", f"{firstname}_{lastname}_{today_str}.csv"), "wb")
        file_content = await personal_data.read()
        f_data.write(file_content)
        f_data.close()
        samples[f'{firstname}_{lastname}'] = api.samples_from_csv(filepath=os.path.join("users_data", f"{firstname}_{lastname}_{today_str}.csv"))
        stats[f'{firstname}_{lastname}'] = models.Stats.from_sample_collection(samples[f"{firstname}_{lastname}"])
        return HTMLResponse(content=content)
    except IOError:
        # Displaying error page if file input handling failed
        f = open("pages/error_upload.html", "r")
        content = f.read()
        f.close()
        return HTMLResponse(content=content)

@app.get("/user/{username}/samples")
def read_samples(username: str, day: Optional[str] = None):
    if username not in samples:
        error_message = {
            "resource_type": "sample",
            "username": username,
            "error_description": "The username is not in the database" 
        }
        raise HTTPException(status_code=404, detail=error_message)
    if day is None:
        res = list(filter(lambda d: d.sampling_date.date() == datetime.today().date(), samples[username]))
        if len(res) == 0:
            raise HTTPException(status_code=404)
        return res
    try:
        return list(filter(lambda d: datetime.strptime(day, "%d-%m-%Y").date() == d.sampling_date.date(), samples[username]))
    except ValueError:
        error_message = {
            "resource_type": "sample",
            "username": username,
            "error_description": "The date input is invalid" 
        }
        raise HTTPException(status_code=400, detail=error_message)

@app.get("/user/{username}/stats")
def read_stats(username: str):
    return stats[username]

@app.get("/users/stats")
def read_stats():
    return models.Stats.from_all_users_samples(samples)

@app.get("/user/{username}/trend/hours_interval")
def read_trend_hours(username: str, h1_string: str, h2_string: str, error: int):
    h1 = datetime.strptime(h1_string, "%d-%m-%Y_%H:%M")
    h2 = datetime.strptime(h2_string, "%d-%m-%Y_%H:%M")
    return models.HourTrend.from_hours(h1,h2,samples[username], error)

@app.get("/user/{username}/trend/days_interval")
def read_trend_days(username: str, day1_string: str, day2_string: str, error: int):
    day1 = datetime.strptime(day1_string, "%d-%m-%Y")
    day2 = datetime.strptime(day2_string, "%d-%m-%Y")
    return models.HourTrend.from_hours(day1,day2,samples[username], error)

@app.get("/user/{username}/trend/months_interval")
def read_trend_months(username: str, month1: int, year1: int, month2: int, year2: int, error: int):
    return models.MonthTrend.from_months(month1, year1, month2, year2, samples[username], error)