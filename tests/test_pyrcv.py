"""Tests for `pyrcv` package."""

import pathlib

import pytest
from click.testing import CliRunner
from numpy.testing import assert_equal

import pyrcv
from pyrcv import RaceData, RaceMetadata, RaceResult, RoundMode
from pyrcv import RoundResult as RR
from pyrcv import cli

from .utils import assert_race_equal

TESTDATA_PATH = pathlib.Path(__file__).parent / "testdata"


FAIRVOTE_BALLOTS = [
    ([1, 2, 3], 625),  # R4
    ([1, 2, 4], 125),  # R4
    ([1, 2, 5], 250),  # R4; Last is any unviable candidate
    ([1, 2, 6], 250),  # R4; Last is any unviable candidate
    ([1, 5, 3], 500),  # R3
    ([1, 5, 4], 500),  # R3
    ([1, 3], 250),
    ([2, 3, 0], 875),  # R4
    ([2, 4], 175),  # R4
    ([2, 5, 0], 350),  # R4; Last is any unviable candidate
    ([2, 6, 0], 350),  # R4; Last is any unviable candidate
    ([3], 1300),
    ([4, 0, 0], 1300),
    ([5, 2, 3], 625),  # R3, R4
    ([5, 2, 4], 125),  # R3, R4
    ([5, 2, 6], 500),  # R3, R4; Last is any unviable candidate
    ([5, 3], 100),  # R3
    ([6, 3, 0], 580),
    ([6, 4], 300),
    ([6, 2, 3], 50),  # R4
    ([6, 2, 4], 10),  # R4
    ([6, 2, 5], 40),  # R4; Last is any unviable candidate
    ([6, 5, 3], 10),  # R3
    ([6, 5, 4], 10),  # R3
]


def test_bad_rounding():
    metadata = RaceMetadata("race", num_winners=1, names=["A", "B"])
    ballots = [[2, 1], [1, 2]]
    votes = [2, 1]
    with pytest.raises(ValueError):
        pyrcv.run_rcv(RaceData(metadata, ballots, votes), round_mode="bad")


def test_2cands_1seat():
    metadata = RaceMetadata("race", num_winners=1, names=["A", "B"])
    ballots = [[2, 1], [1, 2]]
    votes = [2, 1]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes))
    desired = RaceResult(metadata, [RR([0, 1, 2], [2], [], {})])
    assert_race_equal(actual, desired)


def test_2cands_1seat_undervote():
    metadata = RaceMetadata("race", num_winners=1, names=["A", "B"])
    ballots = [[2, 0], [2, 1], [1, 2]]
    votes = [1, 1, 1]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes))
    desired = RaceResult(metadata, [RR([0, 1, 2], [2], [], {})])
    assert_race_equal(actual, desired)


def test_4cands_2seat_undervote():
    metadata = RaceMetadata("race", num_winners=2, names=["A", "B", "C", "D"])
    ballots = [[4, 0], [3, 0], [2, 4], [2, 0], [1, 4], [1, 0]]
    votes = [3, 3, 1, 1, 1, 1]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes))
    desired = RaceResult(
        metadata,
        [
            RR([0, 2, 2, 3, 3], [], [1], {1: {0: 1, 4: 1}}),
            RR([1, 0, 2, 3, 4], [4], [], {}),
            RR([1, 0, 2, 3, 4], [], [2], {2: {0: 2}}),
            RR([3, 0, 0, 3, 4], [3], [], {}),
        ],
    )
    assert_race_equal(actual, desired)


def test_3cands_2seats_1round():
    metadata = RaceMetadata("race", num_winners=2, names=["A", "B", "C"])
    ballots = [[2, 1, 3], [1, 2, 3]]
    votes = [3, 2]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes))
    desired = RaceResult(metadata, [RR([0, 2, 3, 0], [1, 2], [], {2: {3: 1}})])
    assert_race_equal(actual, desired)


def test_3cands_1seat_multiround():
    metadata = RaceMetadata("race", num_winners=1, names=["A", "B", "C"])
    ballots = [[1, 2, 3], [2, 1, 3], [3, 1, 2]]
    votes = [2, 2, 1]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes))
    desired = RaceResult(
        metadata,
        [
            RR([0, 2, 2, 1], [], [3], {3: {1: 1}}),
            RR([0, 3, 2, 0], [1], [], {}),
        ],
    )
    assert_race_equal(actual, desired)


def test_3cands_2seats_multiround():
    metadata = RaceMetadata("race", num_winners=2, names=["A", "B", "C"])
    ballots = [[1, 3, 2], [2, 1, 3], [3, 1, 2], [3, 2, 1]]
    votes = [2, 4, 1, 2]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes))
    desired = RaceResult(
        metadata,
        [
            RR([0, 2, 4, 3], [2], [], {}),
            RR([0, 2, 4, 3], [], [1], {1: {3: 2}}),
            RR([0, 0, 4, 5], [3], [], {}),
        ],
    )
    assert_race_equal(actual, desired)


def test_3cands_2seats_multiround_with_adjust():
    metadata = RaceMetadata("race", num_winners=2, names=["A", "B", "C"])
    ballots = [[1, 3, 2], [2, 1, 3], [3, 2, 1], [3, 2, 1]]
    votes = [2, 5, 1, 2]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes))
    desired = RaceResult(
        metadata,
        [
            RR([0, 2, 5, 3], [2], [], {2: {1: 1}}),
            RR([0, 3, 4, 3], [], [1], {1: {3: 3}}),
            RR([0, 0, 4, 6], [3], [], {}),
        ],
    )
    assert_race_equal(actual, desired)


def test_3cands_2seats_multiround_fractional_round():
    metadata = RaceMetadata("race", num_winners=2, names=["A", "B", "C"])
    ballots = [[1, 3, 2], [2, 1, 3], [3, 1, 2], [3, 2, 1]]
    votes = [2, 4, 1, 2]
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes), RoundMode.FRACTIONAL)
    desired = RaceResult(
        metadata,
        [
            RR([0, 2, 4, 3], [2], [], {2: {1: 0.99999}}),
            RR([0, 2.99999, 3.00001, 3], [], [1], {1: {3: 2.99999}}),
            RR([0, 0, 3.00001, 5.99999], [3], [], {}),
        ],
    )
    assert_race_equal(actual, desired)


def test_fairvote_example():
    """Example from FairVote's website.

    https://fairvote.org/archives/multi_winner_rcv_example/
    """
    metadata = RaceMetadata("race", num_winners=3, names=["A", "B", "C", "D", "E", "F"])
    ballots, votes = zip(*FAIRVOTE_BALLOTS)
    actual = pyrcv.run_rcv(RaceData(metadata, ballots, votes), RoundMode.CEILING)
    desired = RaceResult(
        metadata,
        [
            RR(
                [0, 2500, 1750, 1300, 1300, 1350, 1000],
                [1],
                [],
                {1: {2: 100, 3: 20, 5: 80}},
            ),
            RR(
                [0, 2300, 1850, 1320, 1300, 1430, 1000],
                [],
                [6],
                {6: {2: 100, 3: 580, 4: 300, 5: 20}},
            ),
            RR(
                [0, 2300, 1950, 1900, 1600, 1450, 0],
                [],
                [5],
                {5: {2: 1250, 3: 150, 4: 50}},
            ),
            RR(
                [0, 2300, 3200, 2050, 1650, 0, 0], [2], [], {2: {0: 360, 3: 450, 4: 90}}
            ),
            RR([360, 2300, 2300, 2500, 1740, 0, 0], [3], [], {3: {0: 200}}),
        ],
    )
    assert_race_equal(actual, desired)


def test_validate_and_standardize_ballots_ok():
    ballots = [[1, 0, 0], [1, 2, 0], [1, 2, 3]]
    result = pyrcv.validate_and_standardize_ballots(ballots, num_cands=3)
    assert_equal(result, [[1, 0, 0, 0], [1, 2, 0, 0], [1, 2, 3, 0]])


def test_validate_and_standardize_ballots_ragged():
    ballots = [[1, 0, 0], [1, 2], [1, 2, 3]]
    result = pyrcv.validate_and_standardize_ballots(ballots, num_cands=3)
    assert_equal(result, [[1, 0, 0, 0], [1, 2, 0, 0], [1, 2, 3, 0]])


def test_validate_and_standardize_ballots_bad_data():
    with pytest.raises(ValueError, match=r"Bad value\(s\) on ballots: \[1, 2\]"):
        ballots = [[1, 0, 0], [1, 2, -1], [1, 2, 3]]
        pyrcv.validate_and_standardize_ballots(ballots, num_cands=2)
    with pytest.raises(ValueError, match="Ballot data are not list of lists"):
        pyrcv.validate_and_standardize_ballots([1, 0, 0], num_cands=2)
    with pytest.raises(ValueError, match="Ballot data are not all integers"):
        pyrcv.validate_and_standardize_ballots([[1, 0, 0.5]], num_cands=2)
    with pytest.raises(ValueError, match=r"Ballot has duplicated entry: \[1, 0, 1\]"):
        pyrcv.validate_and_standardize_ballots([[1, 0, 1]], num_cands=2)


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "Show this message and exit." in help_result.output

    testdata = str(TESTDATA_PATH / "transform_testdata.csv")

    result = runner.invoke(cli.main, [testdata])
    assert result.exit_code == 0
    expected = """race: What is your favorite season?
winner(s): Autumn
"""
    assert result.output == expected

    result = runner.invoke(cli.main, [testdata, "--details"])
    assert result.exit_code == 0
    expected = """race: What is your favorite season?
num_winners: 1
candidates: Spring,Summer,Autumn,Winter

Round 0:
 <exhausted>: 0.0
 Spring: 2.0
 Summer: 3.0
 Autumn: 3.0
 Winter: 0.0 -
Round 1:
 <exhausted>: 0.0
 Spring: 2.0 -
 Summer: 3.0
 Autumn: 3.0
 Winter: 0.0
Round 2:
 <exhausted>: 1.0
 Spring: 0.0
 Summer: 3.0 -
 Autumn: 4.0
 Winter: 0.0
Round 3:
 <exhausted>: 2.0
 Spring: 0.0
 Summer: 0.0
 Autumn: 6.0 +
 Winter: 0.0
"""
    assert result.output == expected
