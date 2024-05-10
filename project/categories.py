from typing import Optional
import pandas as pd


class CategoriesCache(dict):
    CSV_COLS = ['transaction_id', 'category']
    def __init__(self, *, file_path) -> None:
        self.file_path = file_path
        super().__init__()

    def read(self) -> None:
        try:
            df = pd.read_csv(self.file_path, usecols=self.CSV_COLS)
        except:
            return
        for r in df.itertuples():
            self[r.__getattribute__(self.CSV_COLS[0])] = r.__getattribute__(self.CSV_COLS[1])
    
    def write(self, category_by_id: dict[str, str]) -> None:
        df = pd.DataFrame.from_dict(category_by_id, orient='index', columns=[self.CSV_COLS[1]])
        df.to_csv(self.file_path, index_label=self.CSV_COLS[0])

    @property
    def is_empty(self):
        return bool(len(self) == 0)