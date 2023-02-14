from typing import Union
from datetime import datetime, time, date
from typing import Union
from enum import Enum

from pydantic import BaseModel

class BloodGlucoseSample(BaseModel):
    value: int
    sampling_date: datetime
    device_name: str
    device_serial_number: str
    recording_type: int
    rapid_acting_insulin_used: bool
    rapid_acting_insulin_qty: Union[int, None] = None
    slow_acting_insulin_used: bool
    slow_acting_insulin_qty: Union[int, None] = None
    meal_eaten: bool
    carbs: Union[int, None] = None
    comments: Union[int, None] = None
    blood_glucose_by_strip: Union[int, None] = None

class TrendState(Enum, str):
    increase = 'increase'
    decrease = 'decrease'
    steady = 'steady'

class Trend(BaseModel):
    state: TrendState
    delta: float

class HourTrend(Trend):
    hours_intervals: tuple[time, time]
    
class DayTrend(Trend):
    days_intervals: tuple[date, date]

class MonthTrend(Trend):
    months_intervals: tuple[int, int]
    are_same_year: bool

class Stats(BaseModel):
    time_range: tuple[datetime, datetime]
    mininum: int
    maximum: int
    stat_range: int
    mean: float
    variance: float
    standard_deviation: float
    overall_samples_size: int
    first_quartile: int
    second_quartile: int
    third_quartile: int
    median: Union[float, int]

# Ajouter les classes sur les objectifs et sur les prédictions