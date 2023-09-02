from typing import Union, Callable, List, Optional, Tuple, Dict
from datetime import datetime, time, date
from enum import Enum
import statistics as stats

from pydantic import BaseModel

class User(BaseModel):
    user_id: str
    firstname: str
    lastname: str
    username: str
    email: str
    devices_list: List[str]

class CreateUser(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str

class UserDataStored(BaseModel):
    user_data_exists: bool
    last_update: Optional[datetime]

class UserDataFileUpdateResponse(BaseModel):
    message: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenDisplay(BaseModel):
    app_name: Optional[str]
    token_value: str
    creation_date: str
    expiration_date: str
    profile_right: bool
    samples_right: bool
    goals_right: bool
    stats_right: bool

class BloodGlucoseSample(BaseModel):
    device_name: str
    device_serial_number: str
    sampling_date: datetime
    value: int

    def __repr__(self) -> str:
        return repr(self.value) + "   " + repr(self.sampling_date) + "   " + self.device_name

class AverageDayParams(BaseModel):
    hours: List[str]
    error: int

class AverageDaySample(BaseModel):
    hour: time
    average_value: float

class UpdatedKey(Enum):
    title = 'title'
    status = 'status'
    start_datetime = 'start_datetime'
    end_datetime = 'end_datetime'

class TrendState(Enum):
    increase = 'increase'
    decrease = 'decrease'
    steady = 'steady'

    @classmethod
    def from_integer(cls, trend_as_integer: int):
        if trend_as_integer == -1:
            return cls.decrease
        elif trend_as_integer == 0:
            return cls.steady
        elif trend_as_integer == 1:
            return cls.increase
        else:
            raise ValueError(f"The integer must be -1, 0 or 1, but it is {trend_as_integer}")
        
    def to_integer(self):
        if self.name == 'decrease':
            return -1
        elif self.name == 'steady':
            return 0
        else:
            return 1

class Trend(BaseModel):
    state: TrendState
    delta: float

class HourTrend(Trend):
    hours_intervals: Tuple[datetime, datetime]

    @classmethod
    def from_hours(cls, h1: datetime, h2: datetime, samples_collection: List[BloodGlucoseSample], error: int):
        filtered_elements = list(filter(lambda e: h1 <= e.sampling_date <= h2, samples_collection))
        first_el, last_el = filtered_elements[0], filtered_elements[len(filtered_elements)-1]
        state = TrendState.steady
        delta = abs(last_el.value - first_el.value)
        if delta - error > 0:
            state = TrendState.increase
        elif delta + error < 0:
            state = TrendState.decrease
        return cls(state=state, delta=delta, hours_intervals=(h1,h2))
    
class DayTrend(Trend):
    days_intervals: Tuple[date, date]

    @classmethod
    def from_days(cls, day1: date, day2: date, samples_collection: List[BloodGlucoseSample], error: int):
        filtered_elements = list(filter(lambda e: day1 <= e.sampling_date.date() <= day2, samples_collection))
        first_el, last_el = filtered_elements[0], filtered_elements[len(filtered_elements)-1]
        state = TrendState.steady
        delta = abs(last_el.value - first_el.value)
        if delta - error > 0:
            state = TrendState.increase
        elif delta + error < 0:
            state = TrendState.decrease
        return cls(state=state, delta=delta, days_intervals=(day1,day2))

class MonthTrend(Trend):
    month_start: Tuple[int, int]
    month_end: Tuple[int, int]
    are_same_year: bool

    @classmethod
    def from_months(cls, mth1: int, yr1: int, mth2: int, yr2: int, samples_collection: List[BloodGlucoseSample], error: int):
        # Comparing month and year values
        interval_fun: Callable[[BloodGlucoseSample], bool] = lambda e: mth1 <= e.sampling_date.month <= mth2 and yr1 <= e.sampling_date.year <= yr2
        filtered_elements = list(filter(interval_fun, samples_collection))
        first_el, last_el = filtered_elements[0], filtered_elements[len(filtered_elements)-1]
        state = TrendState.steady
        delta = abs(last_el.value - first_el.value)
        if delta - error > 0:
            state = TrendState.increase
        elif delta + error < 0:
            state = TrendState.decrease
        return cls(state=state, delta=delta, month_start=(mth1, yr1), month_end=(mth2, yr2), are_same_year=yr1==yr2)

class Stats(BaseModel):
    time_range: Optional[Union[Tuple[str, str], Tuple[datetime, datetime]]]
    minimum: Optional[int]
    maximum: Optional[int]
    stat_range: Optional[int]
    mean:Optional[float]
    variance: Optional[float]
    standard_deviation: Optional[float]
    overall_samples_size: Optional[int]
    first_quartile: Optional[int]
    second_quartile: Optional[int]
    third_quartile: Optional[int]
    median: Optional[Union[float, int]]

    @classmethod
    def from_sample_collection(cls, sample_collection: List[BloodGlucoseSample]):
        values = [s.value for s in sample_collection]
        qts: list = stats.quantiles(values, n=4)
        return cls(
            time_range=(sample_collection[0].sampling_date, sample_collection[len(sample_collection)-1].sampling_date),
            minimum=min(values),
            maximum=max(values),
            stat_range=max(values)-min(values),
            mean=round(stats.fmean(values), 2),
            variance=round(stats.pvariance(values), 2),
            standard_deviation=round(stats.pstdev(values), 2),
            overall_samples_size=len(values),
            first_quartile=qts[0],
            second_quartile=qts[1],
            third_quartile=qts[2],
            median=stats.median(values)
        )
    
    @classmethod
    def from_all_users_samples(cls, all_users_samples: Dict[str, List[BloodGlucoseSample]]):
        # Flatten the users collections
        flatten_collection = [sample for user_collection in all_users_samples.values() for sample in user_collection]
        return cls.from_sample_collection(flatten_collection) 
        

class GoalType(Enum):
    sample = 'sample'
    stats = 'stats'

class GoalStatus(Enum):
    not_started = 'not_started'
    on_going = 'on_going'
    completed = 'completed'

    @classmethod
    def from_integer(cls, status_as_integer: int):
        if status_as_integer == -1:
            return cls.not_started
        elif status_as_integer == 0:
            return GoalStatus.on_going
        elif status_as_integer == 1:
            return GoalStatus.completed
        else:
            raise ValueError("The integer must be -1, 0 or 1, but it is "+ status_as_integer)
    
    def to_integer(self):
        if self.name == 'not_started':
            return -1
        elif self.name == 'on_going':
            return 0
        else:
            return 1

class Goal(BaseModel):
    id: Optional[int]
    title: Optional[str]
    status: Optional[GoalStatus]
    start_datetime: Optional[datetime]
    end_datetime: Optional[datetime]
    average_target: Optional[int]
    trend_target: Optional[TrendState]
    stats_target: Optional[Stats]

class GoalAttr(BaseModel):
    value: Union[int, str, datetime]

class AllUserInformation(BaseModel):
    account: User
    goals: List[Goal]

class Resource(BaseModel):
    resource_name: str
    description: Optional[str]

class Feature(BaseModel):
    title: str
    description: Optional[str]
    http_verb: str
    uri: str
    available: bool

class BlockOfContent(BaseModel):
    title: str
    content: str

class APIDocInfo(BaseModel):
    description: List[BlockOfContent]
    authentification: List[BlockOfContent]
    rights: List[BlockOfContent]

class ReqNewPasswordParameters(BaseModel):
    email_or_username: str

class ChangePasswordParameters(BaseModel):
    new_password: str

class PasswordResponse(BaseModel):
    is_success: bool
    description: str

class Resources(BaseModel):
    id: int
    resource_name: str
    description: Optional[str]

class AdminRole(Enum):
    doc = 'doc'
    user = 'user'
    backup = 'backup'

class SecretSignature(BaseModel):
    id: int
    secret_value: str
    generation_date: str

class UserRole(BaseModel):
    is_admin: bool = False
    admin_roles: Optional[List[AdminRole]] = None