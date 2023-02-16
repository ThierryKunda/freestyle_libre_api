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