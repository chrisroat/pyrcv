"""Implementation of Single Transferable Vote."""

from __future__ import annotations

import collections
import enum
import itertools

import numpy as np
from numpy.typing import ArrayLike

from .types import PyRcvError, RaceData, RaceResult, RoundResult


class RoundMode(enum.Enum):
    r"""How to round a fractional vote threshold to win an election.

    .. math::
       votes\_needed = num\_votes / (num\_candidates + 1)
    """

    CEILING = 1
    """If threshold is a fraction, use the next highest integer.

    Used in test of FairVote data, though technically incorrect when
    result is not a fraction.
    """

    ADD_ONE_FLOOR = 2  # Very close to correct, and easy to understand.
    """Add one.  If threshold is a fraction, use the next lowest integer.

    Easy to understand, as it maintains an integer threshold.  More correct
    than :attr:`CEILING`, as it avoid ties when the result is an integer before
    rounding.  For example, if there are 100 votes, the threshold to win
    should be 51 votes, not 50.
    """

    FRACTIONAL = 3
    """No rounding of fractional threshold, requires :math:`threshold + epsilon` votes.

    Technically, this is the most correct, but leads to lots of fractional votes.
    """


EPSILON = 1e-5


def run_rcv(
    race_data: RaceData, round_mode: RoundMode = RoundMode.ADD_ONE_FLOOR
) -> RaceResult:
    """Run the ranked choice voting algorithm for a single election.

    RCV is a method of voting in which each voter casts a single vote in the form
    of a ranked list.  Winners are determined via an iterative algorithm
    that requires a winner to surpass a threshold (e.g. half the votes in a
    single-winner election).  If no-one surpasses the threshold in an iteration,
    the candidate with the least votes is eliminated and ballots supporting
    the eliminated candidate are adjusted to the next highest ranked
    candidate.

    :param race_data: Full information about the race parameters and votes.
    :param round_mode: The method for rounding the vote threshold.

    :raise ValueError: Raised when round_mode has an unknown value, or when the
            ballot data has the wrong shape or contains bad values.
    :raise PyRcvError: Raised if an error is detected in the calcuations.
    :return: RCV results (winners, losers, vote transfers) for each round in
        the election.
    """
    num_cands = len(race_data.metadata.names)

    # ballots has shape (num_ballots, max_allowed_ranking).
    ballots = validate_and_standardize_ballots(race_data.ballots, num_cands)
    # votes has shape (num_ballots, 1).
    votes = np.array(race_data.votes)[:, None]

    # The number of slots is the valid indicies on a ballot.  Candidates are
    # numbered starting from one, and zero is reserved for empty rankings.
    # Example of ballot which allows 5 rankings, but has 2 empty rankings:
    #   [4, 8, 2, 0, 0]
    num_slots = num_cands + 1

    # weights has the same shape as ballots and describes how a vote is distributed
    # across multiple candidates in a ballot.  It is updated in each iteration of
    # the RCV algorithm, with the constraint that each row (i.e. one ballot) must
    # sum to one.  weights is initialized so that the top-ranked candidate starts
    # with all of the weight.
    weights = np.zeros_like(ballots, float)
    weights[:, 0] = 1

    # The threshold number of votes required to win the election, rounded as
    # requested.
    votes_needed = np.sum(votes) / (race_data.metadata.num_winners + 1)
    if round_mode == RoundMode.CEILING:
        votes_needed = np.ceil(votes_needed)
    elif round_mode == RoundMode.ADD_ONE_FLOOR:
        votes_needed = np.floor(1 + votes_needed)
    elif round_mode == RoundMode.FRACTIONAL:
        votes_needed += EPSILON
    else:
        raise ValueError(f"round_mode is not a value in RoundMode enum: {round_mode}")

    # status is used to represent the current state of a candidate:
    # -1: lost the election
    #  0: still in the running
    #  1: a winner in the election
    status = np.zeros(num_slots, int)
    status[0] = -2  # slot==0 corresponds to empty marks in a ballot, and is not used.

    # valid is the same shape as ballots and keeps track of which candidates
    # on a ballot are still in the running.
    valid = np.ones_like(ballots, bool)

    # At the start of each iteration, `orig`` represents the index (on each ballot)
    # of the highest ranked candidate still in the race.
    orig = _first_nonzero(valid, axis=1)

    round_info = []  # Will contain the full results of each round.

    # Iterate until the required number of winners are found.
    while np.count_nonzero(status > 0) < race_data.metadata.num_winners:
        # The number of votes for each candidate (in ballots) is counted, using the
        # current weights.
        counts = np.bincount(ballots.ravel(), (weights * votes).ravel(), num_slots)
        # Reject (mask) the candidates who have already won or lost.
        counts_masked = np.ma.array(counts, mask=(status != 0))

        # A boolean array indicating the candidate (indices) that have been elected
        # in this round.
        # Ex: [False, False, True, False, True] indicates that candidates 2 and 4
        #     have surpassed the vote threshold on this round.
        # Keep in mind that index==0 is the empty (no vote) candidate.
        elected_mask = counts_masked >= votes_needed

        # Indices of candidates elected in this round.
        elected = []
        # Indices of candidates eliminated in this round.
        eliminated = []
        # Candidates removed from consideration (elected or eliminated)
        to_remove = []
        # Fraction of votes kept by those in `to_remove`.  Winners keep just
        # `votes_needed` votes, while losers keep no votes.
        multipliers = []

        # If the number of viable candidates (elected or still in the running)
        # is the required number of winners, we can just stop now and declare
        # the winners.
        if np.count_nonzero(status >= 0) == race_data.metadata.num_winners:
            # status == 0 are the currently "still in the running" candidates
            elected = np.nonzero(status == 0)[0]
            status[status == 0] = 1
        elif elected_mask.any():
            # New candidates just surpassed the vote threshold, and are removed
            # from the running.
            to_remove = np.nonzero(elected_mask)[0]
            elected = to_remove
            status[to_remove] = 1
            # Newly elected candidates keep only `votes_needed` votes, and pass
            # on excess votes to the next highest-ranked candidate.
            multipliers = [votes_needed / counts_masked[c] for c in to_remove]
        else:
            # Eliminate candidate with fewest votes.
            min_counts = np.where(counts_masked == counts_masked.min())[0]
            # If multiple candidates are tied for last place, select on at random.
            to_remove = [np.random.choice(min_counts)]
            eliminated = to_remove
            status[to_remove] = -1
            # Eliminated candidates pass on all their votes to the next
            # highest-ranked candidates.
            multipliers = [0]

        # Distribute votes from elected/eliminated candidates to the next active
        # lower ranked candidate.  Elected candidates transfer excess votes, while
        # eliminated candidates transfer all votes.
        transfers = {}
        for cand, mult in zip(to_remove, multipliers):
            valid[ballots == cand] = False
            next = _first_nonzero(valid, axis=1)  # Next active candidate on each ballot

            # Ballots where the candidate changed
            o_rows = orig != next
            # Ballots the candidate changed, but where no active candidate remains
            n_rows = o_rows & (next != -1)

            # Votes are transferred to next candidate.
            weights[n_rows, next[n_rows]] = weights[n_rows, orig[n_rows]] * (1 - mult)
            # Votes are transferred from original candidate.
            weights[o_rows, orig[o_rows]] *= mult

            transfers_cand = collections.defaultdict(int)
            slicer = n_rows, next[n_rows]
            for c, v in zip(ballots[slicer], (weights * votes)[slicer]):
                if v:
                    transfers_cand[c] += v

            if transfers_cand:
                transfers[cand] = dict(transfers_cand)
            orig = next

        # Sanity check that the algorithm didn't misplace any votes.  Should not happen.
        if not np.isclose(counts.sum(), votes.sum()):  # pragma: no cover
            raise PyRcvError("Final round count total does not equal original votes")

        round_info.append(
            RoundResult(counts.tolist(), list(elected), list(eliminated), transfers)
        )
    return RaceResult(race_data.metadata, round_info)


def _first_nonzero(arr: ArrayLike, axis: int, invalid_val=-1) -> np.ndarray:
    """Returns the indices of the first non-zero value along an axis."""
    mask = arr != 0
    return np.where(mask.any(axis=axis), mask.argmax(axis=axis), invalid_val)


def validate_and_standardize_ballots(
    ballots: list[list[int]], num_cands: int
) -> np.ndarray:
    """Flush out ballots into a 2-d array using zeros, and check for invalid votes.

    :param ballots: List of ballots, which are lists of ints
    :param num_cands: Number of candidates in the election.
    :return: 2-d array of ballot data
    """

    # Fill out ballots to be the same length.
    def isiter(lst):
        return isinstance(lst, (list, tuple))

    if not isiter(ballots) or not all(isiter(lst) for lst in ballots):
        raise ValueError("Ballot data are not list of lists")
    if not all(isinstance(el, int) for lst in ballots for el in lst):
        raise ValueError("Ballot data are not all integers")

    ballots_flush = list(itertools.zip_longest(*ballots, fillvalue=0))
    ballots = np.array(ballots_flush, dtype=np.int8).T

    # Validate all rankings are for valid candidate indices.
    check_oob(ballots, num_cands)

    # Check there are no duplicate rankings in a ballot.
    np.apply_along_axis(check_dup_1d, axis=1, arr=ballots)

    # Add a 0 at the end of every ballot.
    return np.pad(ballots, ((0, 0), (0, 1)))


def check_oob(ballots: ArrayLike, num_cands: int):
    """Checks that ballot indices are positive and <=num_cands.

    :param ballots: List of ballots, which are lists of ints
    :param num_cands: Number of candidates in the election.
    :raises ValueError: If invalid indices are present, their positions
        are given in the error message.
    """
    ballots = np.asarray(ballots)
    oob_rankings = (ballots < 0) | (ballots > num_cands)
    if oob_rankings.any():
        bad_ballots = oob_rankings.any(axis=1)
        bad_indices = np.nonzero(bad_ballots)[0].tolist()
        raise ValueError(f"Bad value(s) on ballots: {bad_indices}")


def check_dup_1d(ballot: ArrayLike) -> bool:
    """Checks if there are duplicate candidate indicies in a ballot.

    Note that zero constitutes no mark, and duplicate zeros are allowed.

    :param ballot: Ranking of candidate indices, e.g. ``[4,3,1,0,0]``
    :raises ValueError: If duplicate candidate indices present in ballot.
    :return: True if duplicate candidate indices present in ballot, False otherwise.
    """
    unique, counts = np.unique(ballot, return_counts=True)
    has_dup = (counts[unique != 0] > 1).any()
    if has_dup:
        raise ValueError(f"Ballot has duplicated entry: {ballot.tolist()}")
    return has_dup
