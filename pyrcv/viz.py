"""Utilities for creating Sankey plots of RCV results."""

from typing import Tuple

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative

from pyrcv import RaceResult

NODE_PALETTE = qualitative.Dark2  #: Default Sankey diagram node colors.
LINK_PALETTE = qualitative.Set2  #: Default Sankey diagram link colors.


def result_to_sankey_data(
    race_result: RaceResult,
    hide_exhausted=False,
    node_palette=NODE_PALETTE,
    link_palette=LINK_PALETTE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Convert a :class:`pyrcv.types.RaceResult` into data needed for a Sankey diagram.

    A Sankey diagram consists of nodes and links between nodes. Links have
    a value denoting the flow from the source node to the target node. The
    value of a node is the sum of flows into the node minus the flows out
    of the node.

    In a Sankey diagram visualizing an RCV election, there is a node for each candidate
    in each round.  Nodes are associated with a round, have a color, and are labelled
    by their candidate.  Node indexes for a given round/candidate are show in the
    following table:

    .. code-block:: text

                cand_0   cand_1  ...   cand_n-1
                ------  -------       ---------
        round_0:     0,       1, ...,   ncand-1
        round_1: ncand, ncand+1, ..., 2*ncand-1
        ... etc ...

    Links are between nodes in consecutive rounds, and denote how many votes flow
    from one candidate to another - including votes a candidate keeps for themself.  A
    link has a source and a target.  By default, it is colored with the same hue as the
    node it starts from, but with lighter saturation.

    :param race_result: Result of a single RCV race.
    :param hide_exhausted: If True, do not include counts of exhausted ballots,
        Defaults to False.
    :param node_palette: Colors to use for nodes in Sankey diagram.  Should match
        in hue to link_palette.  If there are more candidates then colors, the
        palette is cycled.  Defaults to :const:`NODE_PALETTE`.
    :param link_palette: Colors to use for links between nodes in Sankey diagram.
        Should match in hue to node_palette.  If there are more candidates then colors,
        the palette is cycled.  Defaults to :const:`LINK_PALETTE`.
    :return: Returns two dataframes:

        * Node dataframe with columns ``round``, ``label``, ``color``
        * Link dataframe with columns ``source``, ``target``, ``value``, ``color``
    """
    num_rounds = len(race_result.rounds)

    labels = ["<exhausted>"] + race_result.metadata.names
    num_cands = len(labels)

    node_color = [node_palette[idx % len(node_palette)] for idx in range(num_cands)]
    df_nodes = pd.DataFrame({"label": labels, "color": node_color})
    df_nodes = pd.concat(
        [df_nodes] * (num_rounds), keys=range(num_rounds), names=["round", "id"]
    )
    df_nodes = df_nodes.reset_index()

    data_links = []
    for rnd in range(num_rounds - 1):
        round_result = race_result.rounds[rnd]
        for src in range(num_cands):
            color = link_palette[src % len(link_palette)]
            src_left = round_result.count[src]
            if src in round_result.transfers:
                for tgt, diff in round_result.transfers[src].items():
                    data_links.append((rnd, src, tgt, diff, color))
                    src_left -= diff
            if src_left > 0:  # votes that were not transferred
                data_links.append((rnd, src, src, src_left, color))

    df_links = pd.DataFrame(
        data_links, columns=["round", "source", "target", "value", "color"]
    )

    df_links["source"] += df_links["round"] * num_cands
    df_links["target"] += (df_links["round"] + 1) * num_cands

    if hide_exhausted:
        mask = (df_nodes["id"] % num_cands) == 0
        df_nodes.loc[mask, "color"] = "rgba(0,0,0,0)"
        df_nodes.loc[mask, "label"] = ""

        mask = (df_links["target"] % num_cands) == 0
        df_links.loc[mask, "color"] = "rgba(0,0,0,0)"

    return df_nodes, df_links


def create_sankey_fig(df_nodes: pd.DataFrame, df_links: pd.DataFrame) -> go.Figure:
    """Creates Sankey diagram using data about colors, labels, and vote transfers.

    See :meth:`result_to_sankey_data` for a description of the data.

    :param df_nodes: Dataframe containing columns of node info:
        ``round``, ``label``, ``color``
    :param df_links: Dataframe containing columns of link info:
        ``source``, ``target``, ``value``, ``color``

    :return: Sankey diagram
    """
    sankey = go.Sankey(
        node=dict(
            thickness=10,
            line={"width": 0},
            label=df_nodes["label"],
            color=df_nodes["color"],
            # Add 1 to start indexing from 1 (real people do not like 0-indexing)
            customdata=df_nodes["round"] + 1,
            hovertemplate=(
                "%{label} has %{value:.1~f} votes "
                "in round %{customdata}<extra></extra>"
            ),
        ),
        link=dict(
            source=df_links["source"],
            target=df_links["target"],
            value=df_links["value"],
            color=df_links["color"],
            # For display, add 2 to round:
            # - add 1 because it is the next round that the transfers are counted
            # - add 1 to start indexing from 1 (real people do not like 0-indexing)
            customdata=df_links["round"] + 2,
            hovertemplate=(
                "%{value:.1~f} votes transferred<br />"
                "from %{source.label} to %{target.label}<br />"
                "in round %{customdata}<extra></extra>"
            ),
        ),
        visible=True,
    )

    fig = go.Figure(data=[sankey])
    fig.update_layout(
        margin=dict(l=0, t=0),
    )
    return fig
