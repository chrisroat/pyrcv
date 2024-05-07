"""Common types used in :mod:`pyrcv`."""

from dataclasses import dataclass

from icontract import invariant


class PyRcvError(Exception):
    """Error in pyrcv."""


@dataclass
class RaceMetadata:
    """Specification of a single race.

    :param race_name: Unique name for this race.
    :param num_winners: How many candidates will win the race.
    :param names: List of candidate names.
    """

    race_name: str
    num_winners: int
    names: list[str]

    def __str__(self):
        cands = ",".join(self.names)
        return (
            f"race: {self.race_name}\n"
            f"num_winners: {self.num_winners}\n"
            f"candidates: {cands}"
        )


@invariant(lambda self: len(self.metadata.names) >= max(map(max, self.ballots)))
@invariant(lambda self: len(self.ballots) == len(self.votes))
@dataclass
class RaceData:
    """Voting data for a single race.

    The two main ways to use this class:

    * Each ballot corresponds to one person's vote.  Multiple ballots can be identical,
      and all the entries in votes are 1.  This usage is the most verbose and uses more
      memory, but does correspond to the typical understanding of a ballot.

    * Each ballot corresponds to a unique ordering of the candidates.  All ballots
      are unique.  The entry in :attr:`votes` corresponding to a given ballot indicates
      the number of people who voted in that ordering.  This usage is the most compact
      and uses less memory.

    As an example, the following would be identical in a 2 candidate race with 7 voters:

    .. code-block:: text

        metadata: <elided>
        ballots: [[1,2], [2], [2,1], [2,1], [2], [1], [2, 1]]
        votes: [1, 1, 1, 1, 1, 1, 1]

    .. code-block:: text

        metadata: <elided>
        ballots: [1], [2], [1, 2], [2, 1]
        votes: [1, 2, 1, 3]

    :param metadata: Details about the race.
    :param ballots: A list of candidate rankings.  Each list[int] is an ordering of a
        subset candidate indexes, with the index refering to the list of candidates in
        :attr:`metadata`.
    :param votes: A list of the same length as :attr:`ballots` which denotes the number
        of votes corresponding to each candidate ranking.  The sum of votes corresponds
        to the total number of votes cast.
    """

    metadata: RaceMetadata
    ballots: list[list[int]]
    votes: list[int]


@dataclass
class RoundResult:
    """The full results of a single-transferable voting round.

    :param count: The votes for each candidate.  Candidates are index starting at 1,
        with the index=0 reserved for exhausted ballots.
    :param elected: Candidate indices that won the election by this round.
    :param eliminated: Candidate indices that lost the election by this round.
    :param transfers: Vote counts transferred during this round.  It is a
        two-level map of ``src_cand_index -> tgt_cand_index -> vote_count``
    """

    count: list[float]
    elected: list[int]
    eliminated: list[int]
    transfers: dict[int, dict[int, float]]


@invariant(lambda self: len(set(len(r.count) for r in self.rounds)) < 2)
@invariant(
    lambda self: not self.rounds
    or (len(self.rounds[0].count) == len(self.metadata.names) + 1)
)
@dataclass
class RaceResult:
    """The list of all round results for a single race.

    :param metadata: Details about the race.
    :param rounds: List of results from each round of tabulation.
    """

    metadata: RaceMetadata
    rounds: list[RoundResult]

    def __str__(self):
        def rnd2str(round_result):
            details = []
            names_all = ["<exhausted>"] + self.metadata.names
            for idx, (name, cnt) in enumerate(zip(names_all, round_result.count)):
                name_detail = f" {name}: {cnt}"
                if idx in round_result.elected:
                    name_detail += " +"
                if idx in round_result.eliminated:
                    name_detail += " -"
                details.append(name_detail)
                # Add transfers
            return "\n".join(details)

        round_info = []
        for rnd, round_results in enumerate(self.rounds):
            round_info.extend([f"Round {rnd}:", rnd2str(round_results)])
        rounds = "\n".join(round_info)
        return f"{self.metadata}\n\n{rounds}"
