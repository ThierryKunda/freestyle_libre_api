from enum import Enum
from datetime import datetime
import csv

import requests as req

import os
from models import BloodGlucoseSample, Stats

class SourceType(Enum):
    CSVfile = 'CSVfile'
    sourceUri = 'sourceUri'

def samples_from_csv(data_from: str = SourceType.CSVfile, **query_parameters) -> list[BloodGlucoseSample]:
    res: list[BloodGlucoseSample] = []
    if data_from == SourceType.CSVfile:
        f = open(os.path.join(os.getcwd(), query_parameters['filepath']), newline='')
        reader = csv.reader(f, delimiter=',')
        next(reader)
        for row in reader:
            if row[4] == "-1" or row[4] == "":
                continue
            res.append(BloodGlucoseSample(
                device_name=row[0],
                device_serial_number=row[1],
                sampling_date=datetime.strptime(row[2], "%d-%m-%Y %H:%M"),
                recording_type=row[3],
                value=int(row[4])
            ))
        f.close()
    elif data_from == SourceType.sourceUri:
        pass
    else:
        raise Exception("The source type is not included in the options")
    # Sort by time
    res.sort(key=lambda e: e.sampling_date)
    return res

if __name__ == '__main__':
    my_data = samples_from_csv(SourceType.CSVfile, filepath=os.path.join("tests","glucose_real_data.csv"))
    # for s in my_data:
    #     print(s)
    my_stats = Stats.from_sample_collection(my_data)
    print(my_stats)