class InvalidDataException(Exception):
    """Exception class for invalid data :
    - invalid syntax
    - missing required values
    """
    def __init__(self, message) -> None:
        super().__init__(message)

class DataItemValidator:
    def __init__(
            self, min_columns_amount: int, max_columns_amount: int,
            raise_exception: bool, none_evaluated_values: list[list[str]],
            data: list[str] | None = None, separator: str = ",", contains_void: list[str] | None = None
        ) -> None:
        self.data = data
        self.raise_exception = raise_exception
        self.contains_void = contains_void
        self.min_columns_amount = min_columns_amount
        self.max_columns_amount = max_columns_amount
        self.none_evaluated_values = none_evaluated_values
        self.separator = separator

    def check_data_initialized(self):
        if self.data is None:
            raise ValueError("Data item is not initialized")

    def __getitem__(self, key) -> str | None:
        self.check_data_initialized()
        if self.data[key] in self.none_evaluated_values[key]:
            return self.data[key]
        return None
    
    def size_is_valid(self) -> bool | None:
        self.check_data_initialized()
        data_size = len(self.data)
        if not self.min_columns_amount <= data_size:
            if self.raise_exception:
                raise InvalidDataException(
                "The amount of values does not match the minimum required : {} actual columns < {} minimum columns"
                .format(data_size, self.min_columns_amount)
            )
            else:
                return False
        if not data_size <= self.max_columns_amount:
            if self.raise_exception:
                raise InvalidDataException(
                    "The amount of values does not match the maximum required : {} actual columns > {} maximum columns"
                    .format(data_size, self.max_columns_amount)
                )
            else:
                return False
        return True
    
    def void_is_valid(self) -> bool | None:
        if self.contains_void:
            for i in range(len(self.data)):
                if self.data[i] in self.contains_void[i]:
                    if self.raise_exception:
                        raise ValueError("Some data piece are missing")
                    else:
                        return False
        return True
    
    def set_data(self, new_data: list[str]):
        self.data = new_data

    def exception_is_raised(self):
        return self.raise_exception
    
    def data_is_valid(self) -> bool | None:
        size_v = self.size_is_valid()
        void_v = self.void_is_valid()
        return size_v and void_v