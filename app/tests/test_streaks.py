from datetime import date

from utils.streaks import calculate_streak_stats


def test_streak_counts_consecutive_dates_and_ignores_duplicates():
    current, longest, last = calculate_streak_stats(
        [
            date(2026, 10, 17),
            date(2026, 10, 18),
            date(2026, 10, 18),
            date(2026, 10, 19),
            date(2026, 10, 15),
        ],
        today=date(2026, 10, 19),
    )
    assert current == 3
    assert longest == 3
    assert last == date(2026, 10, 19)


def test_old_streak_is_not_reported_as_current():
    current, longest, last = calculate_streak_stats(
        [date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 4)],
        today=date(2026, 10, 19),
    )
    assert current == 0
    assert longest == 2
    assert last == date(2026, 10, 4)


def test_no_checkins_has_zero_streaks():
    assert calculate_streak_stats([], today=date(2026, 10, 19)) == (0, 0, None)
