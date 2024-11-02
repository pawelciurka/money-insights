from datetime import datetime, timedelta
from typing import Optional
import numpy as np

NOW = datetime.now()


def get_past_month_start_datetime(
    n_months_back: int, reference_date: Optional[datetime] = None
):
    reference_date = reference_date or NOW

    new_month = ((reference_date.month - n_months_back % 12) + 12) % 12
    n_years_back = int(np.floor((reference_date.month - n_months_back) / 12))

    return datetime(year=reference_date.year - n_years_back, month=new_month, day=1)
