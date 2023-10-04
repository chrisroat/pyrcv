=====
Usage
=====

Library
=======

To use pyrcv via python code::

    In [1]: from pyrcv import RaceMetadata, RaceData, run_rcv
    In [2]: metadata = RaceMetadata(
       ...:     "Springfield City Council",
       ...:     num_winners=2,
       ...:     names=["Moe", "Marge", "Edna", "Ned"]
       ...: )
    In [3]: ballots = [[4, 0], [3, 0], [2, 4], [2, 0], [1, 4], [1, 0]]
    In [4]: votes = [3, 3, 1, 1, 1, 1]
    In [5]: race_data = RaceData(metadata, ballots, votes)
    In [6]: result = run_rcv(race_data)
    In [7]: print(actual)

    race: Springfield City Council
    num_winners: 2
    candidates: Moe,Marge,Edna,Ned

    Round 0:
     <exhausted>: 0.0
     Moe: 2.0 -
     Marge: 2.0
     Edna: 3.0
     Ned: 3.0
    Round 1:
     <exhausted>: 1.0
     Moe: 0.0
     Marge: 2.0
     Edna: 3.0
     Ned: 4.0 +
    Round 2:
     <exhausted>: 1.0
     Moe: 0.0
     Marge: 2.0 -
     Edna: 3.0
     Ned: 4.0
    Round 3:
     <exhausted>: 3.0
     Moe: 0.0
     Marge: 0.0
     Edna: 3.0 +
     Ned: 4.0

Command Line
============

The executable ``pyrcv`` is provided which can process elections results from
a CSV file on the command line.  You can download
:download:`example election <example_election.csv>` and try it out as
shown in the following example.

.. code-block:: bash

    $ pyrcv example_election.csv
    race: Rank your 4 favorite pizza toppings
    winner(s): Pepperoni, Chorizo, Sausage
    race: Rank the seasons
    winner(s): Summer

.. click:: pyrcv.cli:main
  :prog: pyrcv

Webserver
===========

A small flask webserver is provided which will process election results from
an uploaded CSV file and make nice visualizations.  To launch the server
locally::

    git clone git@github.com:chrisroat/pyrcv.git
    cd pysvt/server
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python main.py

The server can then be accessed at http://127.0.0.1:8080.   You can download
:download:`example election results<example_election.csv>` to try with
the server.
