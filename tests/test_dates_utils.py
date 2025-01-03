from project.dates_utils import get_past_month_start_datetime
import pytest
from datetime import datetime


@pytest.mark.parametrize(
    ['reference_date', 'n_months_back', 'expected_date'],
    [
        (
            datetime(year=1999, month=2, day=1),
            1,
            datetime(year=1999, month=1, day=1),
        ),
        (
            datetime(year=1999, month=2, day=1),
            2,
            datetime(year=1998, month=12, day=1),
        ),
        (
            datetime(year=1999, month=2, day=1),
            3,
            datetime(year=1998, month=11, day=1),
        ),
        (
            datetime(year=1999, month=2, day=28),
            3,
            datetime(year=1998, month=11, day=1),
        ),
        (
            datetime(year=1999, month=2, day=28),
            15,
            datetime(year=1997, month=11, day=1),
        ),
    ],
)
def test_get_past_month_start_datetime(reference_date, n_months_back, expected_date):
    output_date = get_past_month_start_datetime(
        n_months_back=n_months_back, reference_date=reference_date
    )
    assert expected_date == output_date
