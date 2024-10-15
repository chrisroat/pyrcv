import pathlib

import pytest

import pyrcv
from pyrcv import PyRcvError, RaceData
from pyrcv import RaceMetadata as RM

PATH = pathlib.Path(__file__).parent / "testdata"

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
METADATA = RM("What is your favorite season?", 1, SEASONS)

PARSE_HEADER_DATA = [
    (["Q0 [A00]"], [(RM("Q0", 1, ["A00"]), slice(0, 1))]),
    (["T", "Q0 [A00]", "Q0 [A01]"], [(RM("Q0", 1, ["A00", "A01"]), slice(1, 3))]),
    (["Q0 [A00]", "Q0 [A01]"], [(RM("Q0", 1, ["A00", "A01"]), slice(0, 2))]),
    (
        ["Q0 [A00]", "Q0 [A01]", "Q1 [A10]", "Q1 [A11]"],
        [
            (RM("Q0", 1, ["A00", "A01"]), slice(0, 2)),
            (RM("Q1", 1, ["A10", "A11"]), slice(2, 4)),
        ],
    ),
    (
        ["T", "Q0 [A00]", "Q0 [A01]", "T", "Q1 [A10]", "Q1 [A11]", "T"],
        [
            (RM("Q0", 1, ["A00", "A01"]), slice(1, 3)),
            (RM("Q1", 1, ["A10", "A11"]), slice(4, 6)),
        ],
    ),
    (
        ["Q0 (2 winners) [A00]", "Q0 (2 winners) [A01]", "Q0 (2 winners) [A02]"],
        [(RM("Q0 (2 winners)", 2, ["A00", "A01", "A02"]), slice(0, 3))],
    ),
    (
        [
            "Q0 (2 winners) Translated0 (2 FooBar) [A00]",
            "Q0 (2 winners) Translated0 (2 FooBar) [A01]",
            "Q0 (2 winners) Translated0 (2 FooBar) [A02]",
        ],
        [
            (
                RM("Q0 (2 winners) Translated0 (2 FooBar)", 2, ["A00", "A01", "A02"]),
                slice(0, 3),
            )
        ],
    ),
    (["Q0 [A00] "], []),
    (["Q0[A00]"], []),
    (["Q0  [A00]"], [(RM("Q0", 1, ["A00"]), slice(0, 1))]),
    (["Q0 (2  winners) [A00]"], [(RM("Q0 (2  winners)", 2, ["A00"]), slice(0, 1))]),
    (["Q0  (2 winners) [A00]"], [(RM("Q0  (2 winners)", 2, ["A00"]), slice(0, 1))]),
    (["Q0  (2 winners)  [A00]"], [(RM("Q0  (2 winners)", 2, ["A00"]), slice(0, 1))]),
    (["Q0 (2 winners) [A00]"], [(RM("Q0 (2 winners)", 2, ["A00"]), slice(0, 1))]),
    (["Q0 (2 WINNERS) [A00]"], [(RM("Q0 (2 WINNERS)", 2, ["A00"]), slice(0, 1))]),
    (["Q0 (2 Winners) [A00]"], [(RM("Q0 (2 Winners)", 2, ["A00"]), slice(0, 1))]),
    (["Q0 (2 winner) [A00]"], [(RM("Q0 (2 winner)", 2, ["A00"]), slice(0, 1))]),
    (["Q0 (2 WINNER) [A00]"], [(RM("Q0 (2 WINNER)", 2, ["A00"]), slice(0, 1))]),
    (["Q0 (2 Winner) [A00]"], [(RM("Q0 (2 Winner)", 2, ["A00"]), slice(0, 1))]),
]


@pytest.mark.parametrize("header,expected", PARSE_HEADER_DATA)
def test_parse_header(header, expected):
    assert pyrcv.parse_header(header) == expected


def test_google_form_csv():
    actual = pyrcv.parse_google_form_csv(PATH / "transform_testdata.csv")
    expected = [
        RaceData(
            METADATA,
            [
                [1, 0, 0, 0],
                [1, 3, 2, 4],
                [2, 0, 0, 0],
                [2, 3, 4, 1],
                [3, 1, 4, 2],
                [3, 2, 4, 1],
            ],
            [1, 1, 1, 2, 1, 2],
        )
    ]

    assert actual == expected


def test_google_form_csv_weighted():
    actual = pyrcv.parse_google_form_csv(PATH / "transform_weighted_testdata.csv")
    expected = [
        RaceData(
            METADATA,
            [
                [1, 0, 0, 0],
                [1, 3, 2, 4],
                [2, 0, 0, 0],
                [2, 3, 4, 1],
                [3, 1, 4, 2],
                [3, 2, 4, 1],
            ],
            [3, 1, 2, 3, 4, 3],
        )
    ]

    assert actual == expected


def test_coerce_int():
    actual = pyrcv.parse_google_form_csv(PATH / "transform_int_testdata.csv")
    expected = [RaceData(METADATA, [[3, 2, 4, 1]], [1])]
    assert actual == expected


def test_coerce_bad_data():
    with pytest.raises(PyRcvError, match="Could not determine number: 1st2nd"):
        pyrcv.parse_google_form_csv(PATH / "transform_indeterminate_testdata.csv")
    with pytest.raises(ValueError, match="Cannot use float for candidate index: 0.5"):
        pyrcv.parse_google_form_csv(PATH / "transform_float_testdata.csv")
