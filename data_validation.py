import numpy as np
import pandas as pd
import pandera as pa
from pandera.typing import Series, Index, DataFrame

class InvalidDataException(Exception):
    """Exception class for invalid data :
    - invalid syntax
    - missing required values
    """
    def __init__(self, message) -> None:
        super().__init__(message)

def positive_value(v):
    return v >= 0

user_data_schema = pa.DataFrameSchema({
    "Appareil": pa.Column(str),
    "Numéro de série": pa.Column(str),
    "Horodatage de l'appareil": pa.Column(str),
    "Type d'enregistrement": pa.Column(int),
    "Historique de la glycémie mg/dL": pa.Column(float, pa.Check(positive_value), nullable=True),
    "Numérisation de la glycémie mg/dL": pa.Column(float, pa.Check(positive_value), nullable=True),
    "Insuline à action rapide sans valeur numérique": pa.Column(str, nullable=True),
    "Insuline à action rapide (unités)": pa.Column(float, nullable=True),
    "Alimentation sans valeur numérique": pa.Column(str, nullable=True),
    "Glucides (grammes)": pa.Column(float, pa.Check(positive_value), nullable=True),
    "Glucides (portions)": pa.Column(float, pa.Check(positive_value), nullable=True),
    "Insuline à action longue sans valeur numérique": pa.Column(str, nullable=True),
    "Insuline à action longue (unités)": pa.Column(float, nullable=True),
    "Remarques": pa.Column(str, nullable=True),
    "Glycémie par bandelette mg/dL": pa.Column(float, pa.Check(positive_value), nullable=True),
    "Cétone mmol/L": pa.Column(float, nullable=True),
    "Insuline repas (unités)": pa.Column(float, nullable=True),
    "Correction insuline (unités)": pa.Column(float, coerce=True, nullable=True),
    "Insuline modifiée par l'utilisateur (unités)": pa.Column(float, nullable=True)
},
coerce=True,
strict=True)

def convert_insulin(value: str) -> np.float64:
        if value == "":
            return np.nan
        v_formatted = value.replace(",", ".")
        return np.float64(float(v_formatted))


if __name__ == "__main__":
    df = pd.read_csv("./tests/glucose_real_data.csv", header=0, low_memory=False, converters={
        "Insuline à action longue (unités)": convert_insulin,
        "Insuline à action rapide (unités)": convert_insulin,
        }
    )
    user_data_schema.validate(df)