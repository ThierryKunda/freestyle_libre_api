from typing import Union, Callable
from datetime import datetime, time, date
from enum import Enum
import statistics as stats

from pydantic import BaseModel

class BloodGlucoseSample(BaseModel):
    device_name: str
    device_serial_number: str
    sampling_date: datetime
    recording_type: int
    value: int

    def __repr__(self) -> str:
        return repr(self.value) + "   " + repr(self.sampling_date) + "   " + self.device_name

class TrendState(Enum):
    increase = 'increase'
    decrease = 'decrease'
    steady = 'steady'

class Trend(BaseModel):
    state: TrendState
    delta: float

class HourTrend(Trend):
    hours_intervals: tuple[datetime, datetime]

    @classmethod
    def from_hours(cls, h1: datetime, h2: datetime, samples_collection: list[BloodGlucoseSample], error: int):
        filtered_elements = list(filter(lambda e: h1 <= e.sampling_date <= h2, samples_collection))
        first_el, last_el = filtered_elements[0], filtered_elements[len(filtered_elements)-1]
        state = TrendState.steady
        delta_with_error = abs(last_el.value - first_el.value) + error
        if delta_with_error > 0:
            state = TrendState.increase
        elif delta_with_error < 0:
            state = TrendState.decrease
        return cls(state=state, delta=delta_with_error, hours_intervals=(h1,h2))
    
class DayTrend(Trend):
    days_intervals: tuple[date, date]

    @classmethod
    def from_days(cls, day1: date, day2: date, samples_collection: list[BloodGlucoseSample], error: int):
        filtered_elements = list(filter(lambda e: day1 <= e.sampling_date.date() <= day2, samples_collection))
        first_el, last_el = filtered_elements[0], filtered_elements[len(filtered_elements)-1]
        state = TrendState.steady
        delta_with_error = abs(last_el.value - first_el.value) + error
        if delta_with_error > 0:
            state = TrendState.increase
        elif delta_with_error < 0:
            state = TrendState.decrease
        return cls(state=state, delta=delta_with_error, days_intervals=(day1,day2))

class MonthTrend(Trend):
    month_start: tuple[int, int]
    month_end: tuple[int, int]
    are_same_year: bool

    @classmethod
    def from_months(cls, mth1: int, yr1: int, mth2: int, yr2: int, samples_collection: list[BloodGlucoseSample], error: int):
        # Comparing month and year values
        interval_fun: Callable[[BloodGlucoseSample], bool] = lambda e: mth1 <= e.sampling_date.month <= mth2 and yr1 <= e.sampling_date.year <= yr2
        filtered_elements = list(filter(interval_fun, samples_collection))
        first_el, last_el = filtered_elements[0], filtered_elements[len(filtered_elements)-1]
        state = TrendState.steady
        delta_with_error = abs(last_el.value - first_el.value) + error
        if delta_with_error > 0:
            state = TrendState.increase
        elif delta_with_error < 0:
            state = TrendState.decrease
        return cls(state=state, delta=delta_with_error, month_start=(mth1, yr1), month_end=(mth2, yr2), are_same_year=yr1==yr2)

class Stats(BaseModel):
    time_range: tuple[datetime, datetime]
    minimum: int
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

    @classmethod
    def from_sample_collection(cls, sample_collection: list[BloodGlucoseSample]):
        values = [s.value for s in sample_collection]
        qts: list = stats.quantiles(values, n=4)
        return cls(
            time_range=(sample_collection[0].sampling_date, sample_collection[len(sample_collection)-1].sampling_date),
            minimum=min(values),
            maximum=max(values),
            stat_range=max(values)-min(values),
            mean=stats.fmean(values),
            variance=stats.pvariance(values),
            standard_deviation=stats.pstdev(values),
            overall_samples_size=len(values),
            first_quartile=qts[0],
            second_quartile=qts[1],
            third_quartile=qts[2],
            median=stats.median(values)
        )
    
    @classmethod
    def from_all_users_samples(cls, all_users_samples: dict[str, list[BloodGlucoseSample]]):
        # Flatten the users collections
        flatten_collection = [sample for user_collection in all_users_samples.values() for sample in user_collection]
        return cls.from_sample_collection(flatten_collection) 
        

# Ajouter les classes sur les objectifs et sur les prédictions