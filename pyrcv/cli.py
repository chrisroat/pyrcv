"""Script to tabulate single-transferable vote results from a csv file.

The format required is parsed in the function
:func:`pyrcv.transform.parse_google_form_csv`.
"""

from typing import TextIO

import click

import pyrcv
from pyrcv import RoundMode


@click.command()
@click.argument(
    "csvfile",
    type=click.File(),
)
@click.option("--details", is_flag=True, help="Include round-by-round results.")
@click.option(
    "--round_mode",
    type=click.Choice(RoundMode._member_names_, case_sensitive=False),
    default=RoundMode.ADD_ONE_FLOOR.name,
    show_default=True,
    help=(
        "How to round a fractional vote threshold during tabulation. "
        "The default should be used for most cases."
    ),
)
def main(csvfile: TextIO, details: bool, round_mode: RoundMode):
    """Tabulates results of single-transferable vote elections stored in CSVFILE."""
    races = pyrcv.parse_google_form_csv(csvfile)
    round_mode = pyrcv.RoundMode[round_mode]

    for race in races:
        result = pyrcv.run_rcv(race, round_mode)

        if details:
            print(result)
        else:
            print(f"race: {race.metadata.race_name}")
            names = result.metadata.names
            # -1 because the elected indexing starts from 1.
            winners = ", ".join(
                [names[e - 1] for r in result.rounds for e in r.elected]
            )
            print(f"winner(s): {winners}")

    return 0


if __name__ == "__main__":
    main()  # pragma: no cover
