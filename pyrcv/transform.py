"""Utilities to convert a csv format from Google Forms into pyrcv standard format."""

import re
from typing import Tuple

import numpy as np
import pandas as pd
from pandas._typing import FilePath, ReadCsvBuffer

from .types import PyRcvError, RaceData, RaceMetadata

QUESTION_PATTERN = re.compile(r"^(?P<question>.*?)" r"\s*? " r"\[(?P<option>.*)\]$")

WINNERS_PATTERN = re.compile(r"\((?P<num_winners>\d+)\s+(winners?|WINNERS?|Winners?)\)")


def parse_google_form_csv(
    buffer: FilePath | ReadCsvBuffer[bytes] | ReadCsvBuffer[str],
) -> list[RaceData]:
    """Parses race and ballot info from Googe Form CSV results file.

    The required format is one header line, followed by one line for each ballot.
    The column headers are parsed to determine the races and candidates.  For
    example, the following represents two races, one with 3 candidates and
    one with 2 candidates:

    Mayor [Abe], Mayor [Betty], Mayor [Chris], Police Chief [Alice], Police Chief [Bob]

    Each ballot should provide a numerical ranking within each race.  A ballot cannot
    contain duplicate values within a single race.  Using the example above, some
    valid ballots are:

    1, 2, 1, 2, 3  # Can use raw numbers
    1st, 2nd, 1st, 2nd, 3rd  # Can use ordinals
    1st, 2nd,,,, 1st  # Does not rank Chris or Alice for Police Chief.
    2nd,, 1st, 2nd, 3rd  # Gap in ranking Mayoral race.  Gaps are OK.

    An example invalid ballot would be:
    1, 1, 2, 1, 3  # Duplicate ranking in Mayor race.

    :param buffer: CSV-parseable data in the format described above.
    :return: List containing an entry for each race parsed from the CSV file.
    """
    df = pd.read_csv(buffer)
    race_infos = []

    weights = df["weight"].values if "weight" in df else None

    for metadata, slice_ in parse_header(df.columns):
        goog = df.iloc[:, slice_].map(_coerce).values
        goog = np.ma.array(goog, mask=(goog == 0))

        argsort = goog.argsort(axis=1)
        mask = np.take_along_axis(goog.mask, argsort, axis=1)
        ballots = np.ma.array(argsort, mask=mask) + 1
        ballots = ballots.filled(0)
        if weights is not None:
            ballots = np.repeat(ballots, weights, axis=0)

        ballots, votes = np.unique(ballots, axis=0, return_counts=True)
        race_infos.append(RaceData(metadata, ballots.tolist(), votes.tolist()))
    return race_infos


def parse_header(header: list[str]) -> list[Tuple[RaceMetadata, slice]]:
    """Parse header row list into metadata and a column slices for each race.

    The Google Form header pattern is the race, followed by one of the options for
    that race in brackets.  Adjacent columns for the same race have the same text,
    but different options.  There also can be an optional parenthetical
    indicating the number of winners is allowed between the race and the option;
    if this parenthetical is missing, the race is assumed to be single-winner.

        :param header: Header row from CSV file
        :return: List of tuples, one for each race.  The tuple contains
            :class:`RaceMetadata` and a slice indicating the columns corresponding
            to the options for the race.

    Examples header values:

      * ``What is your favorite season? [Spring]``
      * ``City Council (4 winners) [Darth Vader]``
      * ``Mayor (1 winner) [Luke Skywalker]``
    """
    current_question = None
    current_options = []

    questions = []
    options = []
    num_winners_list = []
    starts = []
    ends = []
    for col_idx, col in enumerate(header):
        question_match = QUESTION_PATTERN.match(col)
        if question_match:
            question = question_match.group("question").strip()
            option = question_match.group("option").strip()
            if question != current_question:
                if current_question is not None:
                    ends.append(col_idx)
                    options.append(current_options)
                    current_options = []

                winners_match = WINNERS_PATTERN.search(question)
                if winners_match:
                    num_winners = int(winners_match.group("num_winners"))
                else:
                    num_winners = 1

                questions.append(question)
                num_winners_list.append(num_winners)
                starts.append(col_idx)
                current_question = question
            current_options.append(option)
        else:
            if current_question is not None:
                current_question = None
                ends.append(col_idx)
                options.append(current_options)
                current_options = []

    if current_question is not None:
        ends.append(col_idx + 1)
        options.append(current_options)

    num_questions = len(questions)
    assert len(options) == num_questions, options
    assert len(starts) == num_questions, starts
    assert len(ends) == num_questions, ends

    return [
        (RaceMetadata(q, w, o), slice(s, e))
        for q, w, o, s, e in zip(questions, num_winners_list, options, starts, ends)
    ]


def _coerce(x):
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        if np.isnan(x):
            return 0
        else:
            raise ValueError(f"Cannot use float for candidate index: {x}")
    numbers = re.findall(r"(\d+)[st|nd|rd|th]?", x)
    if not numbers or len(numbers) > 1:
        raise PyRcvError(f"Could not determine number: {x}")
    return int(numbers[0])
