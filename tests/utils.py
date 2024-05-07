"""Utilities for testing."""

from numpy.testing import assert_allclose, assert_equal


def assert_race_equal(actual, desired):
    assert len(actual.rounds) == len(desired.rounds)
    for r, (ar, dr) in enumerate(zip(actual.rounds, desired.rounds)):
        assert_round_equal(ar, dr, err_msg=f"round {r}")


def assert_round_equal(actual, desired, err_msg):
    assert_allclose(actual.count, desired.count, err_msg=f"{err_msg} count")
    assert_equal(actual.elected, desired.elected, err_msg=f"{err_msg} elected")
    assert_equal(actual.eliminated, desired.eliminated, err_msg=f"{err_msg} eliminated")
    assert_round_dict_equal(
        actual.transfers, desired.transfers, err_msg=f"{err_msg} transfers"
    )


def assert_round_dict_equal(actual, desired, level=0, err_msg=None):
    if actual == desired:
        return

    actual_keys = set(actual.keys())
    desired_keys = set(desired.keys())

    actual_extra = actual_keys - desired_keys
    assert (
        not actual_extra
    ), f"{err_msg} extra actual keys level={level}: {actual_extra}"

    desired_extra = desired_keys - actual_keys
    assert (
        not desired_extra
    ), f"{err_msg} extra desired keys level={level}: {desired_extra}"

    for key in actual_keys:
        if level == 0:
            assert_round_dict_equal(
                actual[key], desired[key], level=1, err_msg=f"{err_msg} key={key}"
            )
        else:
            assert_allclose(actual[key], desired[key], err_msg=f"{err_msg} key={key}")
