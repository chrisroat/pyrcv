=====
pyrcv
=====


.. image:: https://img.shields.io/pypi/v/pyrcv.svg
        :target: https://pypi.python.org/pypi/pyrcv
        :alt: PyPi Status

.. image:: https://github.com/chrisroat/pyrcv/actions/workflows/ci.yml/badge.svg
        :target: https://github.com/chrisroat/pyrcv/actions/workflows/ci.yml
        :alt: Test Status

.. image:: https://readthedocs.org/projects/pyrcv/badge/?version=latest
        :target: https://pyrcv.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


Python project for adjudicating ranked choice voting elections using the
single transferable vote (STV) method.  For more information on ranked
choice voting, visit the `FairVote website on RCV`_.

The project also contains a small flask server for adjudicating and visualizing
election results from a CSV file.  It is automatically deployed at at `pyrcv.org`_

* Free software: GNU General Public License v3
* Documentation: https://pyrcv.readthedocs.io.


Features
--------

* General standards and APIs for voting data and vote tabulation.
* Tabulation of ranked-choice elections using the single-transferable-vote (STV) method.
* Support for both single-winner and multi-winner contests.
* Generation of Sankey diagram showing the flow of vote counts through the
  rounds of a multi-round election.
* Parser for converting Google Form based election output to voting data standard format.
* Web server which processes CSV data output from a Google Form based election, and
  displays winners and a Sankey diagram.


Credits
-------

Inspired by FairVote_ and CalRCV_.  FairVote's examples were extremely helpful for
development and correctness-testing.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _FairVote website on RCV: https://fairvote.org/our-reforms/ranked-choice-voting/
.. _pyrcv.org: https://www.pyrcv.org
.. _FairVote: https://fairvote.org/
.. _CalRCV: https://www.calrcv.org/
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
