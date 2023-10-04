import pandas as pd
import pytest

import pyrcv
from pyrcv import RaceMetadata, RaceResult
from pyrcv import RoundResult as RR

TESTDATA = [
    (False, "<exhausted>", pyrcv.NODE_PALETTE[:4]),
    (True, "", ["rgba(0,0,0,0)"] + pyrcv.NODE_PALETTE[1:4]),
]


@pytest.mark.parametrize("hide_exhausted, label_exhausted, node_colors", TESTDATA)
def test_results_to_sankey(hide_exhausted, label_exhausted, node_colors):
    names = ["A", "B", "C"]
    race_result = RaceResult(
        RaceMetadata("race", 2, names),
        [
            RR([0, 2, 5, 3], [2], [], {2: {1: 1}}),
            RR([0, 3, 4, 3], [], [1], {1: {3: 3}}),
            RR([0, 0, 4, 6], [3], [], {}),
        ],
    )
    df_nodes, df_links = pyrcv.result_to_sankey_data(
        race_result, hide_exhausted=hide_exhausted
    )

    df_nodes_desired = pd.DataFrame(
        {
            "round": [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2],
            "id": [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3],
            "label": ([label_exhausted] + names) * 3,
            "color": node_colors * 3,
        }
    )
    df_links_desired = pd.DataFrame(
        {
            "round": [0, 0, 0, 0, 1, 1, 1],
            "source": [1, 2, 2, 3, 5, 6, 7],
            "target": [5, 5, 6, 7, 11, 10, 11],
            "value": [2, 1, 4, 3, 3, 4, 3],
            "color": [pyrcv.LINK_PALETTE[i] for i in [1, 2, 2, 3, 1, 2, 3]],
        }
    )

    pd.testing.assert_frame_equal(df_nodes, df_nodes_desired, check_like=True)
    pd.testing.assert_frame_equal(df_links, df_links_desired, check_like=True)

    # Just make sure this executes (not sure how to test figure generation)
    fig = pyrcv.create_sankey_fig(df_nodes, df_links)
    assert fig is not None
