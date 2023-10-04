import io
import json

import plotly
from flask import Flask, render_template, request, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField

import pyrcv

app = Flask(__name__)
app.config["WTF_CSRF_ENABLED"] = False


@app.context_processor
def inject_version():
    return dict(pyrcv_version=pyrcv.__version__)


class UploadForm(FlaskForm):
    results_csv = FileField(
        "Election Results CSV File",
        validators=[FileRequired(), FileAllowed(["csv"], "CSV Files only!")],
    )
    hide_exhausted = BooleanField("Hide exhausted ballots in visualization")


@app.route("/instructions")
def instructions():
    return render_template("instructions.html")


@app.route("/", methods=["GET", "POST"])
def index():
    form = UploadForm()

    if request.method == "POST":
        hide_exhausted = form.hide_exhausted.data
        file_storage = form.results_csv.data
        filename = file_storage.filename

        buffer = io.StringIO(
            file_storage.read().decode("latin-1"),
            newline=None,
        )
        data = election_results_viz_data(buffer, hide_exhausted=hide_exhausted)
        return render_template("results.html", filename=filename, data=data)

    return render_template("index.html", form=form)


@app.route("/example")
def example():
    root = request.url_root
    filename = "example_election.csv"
    url = root + url_for("static", filename=filename)
    data = election_results_viz_data(url)
    return render_template("example.html", filename=filename, data=data)


def election_results_viz_data(buffer, hide_exhausted=False):
    races = pyrcv.parse_google_form_csv(buffer)
    data = []
    for race in races:
        result = pyrcv.run_rcv(race)
        names = result.metadata.names

        # -1 because the elected indexing starts from 1.
        winners = [names[e - 1] for r in result.rounds for e in r.elected]

        df_nodes, df_links = pyrcv.result_to_sankey_data(
            result, hide_exhausted=hide_exhausted
        )
        fig = pyrcv.create_sankey_fig(df_nodes, df_links)
        fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        data.append({"metadata": result.metadata, "winners": winners, "figure": fig})

    return data


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
