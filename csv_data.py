import os

from enum import Enum
from datetime import datetime
import pandas as pd
from pandera.errors import SchemaError

from models.resources import BloodGlucoseSample, Stats
from data_validation import convert_insulin, user_data_schema
class SourceType(Enum):
    CSVfile = 'CSVfile'
    sourceUri = 'sourceUri'

def samples_from_csv(data_from: str = SourceType.CSVfile, **query_parameters) -> list[BloodGlucoseSample] | None:
    res: list[BloodGlucoseSample] = []
    if data_from == SourceType.CSVfile:
        df = pd.read_csv(query_parameters["filepath"], sep=',', header=1, parse_dates=[2], date_format="%d-%m-%Y %H:%M", low_memory=False, converters={
        "Insuline à action longue (unités)": convert_insulin,
        "Insuline à action rapide (unités)": convert_insulin,
        })
        try:
            user_data_schema.validate(df)
        except SchemaError:
            return None
        glucose_samples = df.iloc[:, :5].dropna()
        glucose_samples.sort_values(inplace=True, by="Horodatage de l'appareil")
        return [
            BloodGlucoseSample(device_name=s[0], device_serial_number=s[1], sampling_date=s[2].to_pydatetime(), value=s[4])
            for s in glucose_samples.values.tolist()
        ]
    elif data_from == SourceType.sourceUri:
        pass
    else:
        raise Exception("The source type is not included in the options")
    # Sort by time
    res.sort(key=lambda e: e.sampling_date)
    return res

if __name__ == '__main__':
    # v = DataItemValidator(5, 19, True, [["", "-1"] if i == 4 else [] for i in range(20)])
    my_data = samples_from_csv(SourceType.CSVfile, filepath=os.path.join("users_data","Gerard_Depardieu_02-04-2023.csv"))
    my_stats = Stats.from_sample_collection(my_data)
    print(my_stats)