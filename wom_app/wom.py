import logging
import os.path
import pickle
import re
from typing import Optional
import urllib.request

import pandas as pd

from flask import Blueprint, current_app, render_template, request

from wom_app.survery import Survery, SurveyData
from wom_app.utils import fig2png_Response, fig2png_base64, parse_form


_log = logging.getLogger(__name__)

bp = Blueprint("wom", __name__, url_prefix="/wom")


@bp.route("/<election>/clustermap", methods=["GET", "POST"])
def clustermap(election: str):
    answers = parse_form(request.form) if request.method == "POST" else None
    with Wom(election, cacheDir=current_app.instance_path) as wom:
        return fig2png_Response(wom.plot_clustermap(answers))


@bp.route("/<election>/pca", methods=["GET", "POST"])
def pca(election: str):
    answers = parse_form(request.form) if request.method == "POST" else None
    with Wom(election, cacheDir=current_app.instance_path) as wom:
        return fig2png_Response(wom.plot_pca(answers).scatter)


@bp.route("/<election>/questions")
def questions(election: str):
    with Wom(election, cacheDir=current_app.instance_path) as wom:
        return render_template(
            "questions.html",
            election=election,
            questions=wom.data.questions,
        )


@bp.route("/<election>/", methods=["GET"], endpoint="election")
@bp.route("/<election>/results", methods=["POST"])
def results(election: str):
    answers = parse_form(request.form) if request.method == "POST" else None
    with Wom(election, cacheDir=current_app.instance_path) as wom:
        cluster_plot = fig2png_base64(wom.plot_clustermap(answers))
        pca_plots = wom.plot_pca(answers)
        scatter_plot = fig2png_base64(pca_plots.scatter)
        component_0 = fig2png_base64(pca_plots.component_0)
        component_1 = fig2png_base64(pca_plots.component_1)

        return render_template(
            "results.html",
            show_link=answers is None,
            election=election,
            cluster_plot=cluster_plot,
            scatter_plot=scatter_plot,
            component_0=component_0,
            component_1=component_1,
        )


@bp.route("/")
def home():
    return render_template(
        "elections.html",
        elections=[
            "sachsen2024",
            "thueringen2024",
            "europawahl2024",
            "bayern2023",
            "hessen2023",
            "bremen2023",
            "berlin2023",
            "niedersachsen2022",
            "nordrheinwestfalen2022",
            "schleswigholstein2022",
            "saarland2022",
            "bundestagswahl2021",
        ],
    )


def _get_election_data(election: str, cacheDir: Optional[str]) -> SurveyData:
    cacheFile = (
        os.path.join(cacheDir, election + ".pkl") if cacheDir is not None else None
    )

    if cacheFile is not None:
        try:
            with open(cacheFile, "rb") as f:
                data = pickle.load(f)
                _log.info(f"Using data from {cacheFile} for {election}")
                return data
        except OSError as e:
            _log.info(f"Couldn't read data from {cacheFile} for {election}: {e}")

    data = _fetch_election_data(election)

    if cacheFile is not None:
        try:
            with open(cacheFile, "wb") as f:
                pickle.dump(data, f)
        except OSError as e:
            _log.info(f"Couldn't write data to {cacheFile} for {election}: {e}")

    return data


def _fetch_election_data(election: str) -> SurveyData:
    data: str
    data = (
        urllib.request.urlopen(
            f"https://www.wahl-o-mat.de/{election}/app/definitionen/module_definition.js"
        )
        .read()
        .decode()
    )

    if "WOMT_aThesen" not in data:
        data = (
            urllib.request.urlopen(
                f"https://archiv.wahl-o-mat.de/{election}/app/definitionen/module_definition.js"
            )
            .read()
            .decode()
        )

    titles = re.findall(
        r"^WOMT_aThesen\[\d+\]\[\d+\]\[0] = \'(.+?)\';$",
        data,
        re.MULTILINE,
    )
    questions = re.findall(
        r"^WOMT_aThesen\[\d+\]\[\d+\]\[1] = \'(.+?)\';$",
        data,
        re.MULTILINE,
    )
    question_df = pd.DataFrame(
        zip(titles, questions),
        columns=["title", "question"],
    )

    party_long = re.findall(
        r"^WOMT_aParteien\[\d+\]\[\d+\]\[0] ?= ?\'(.+?)\';$",
        data,
        re.MULTILINE,
    )
    party_short = re.findall(
        r"^WOMT_aParteien\[\d+\]\[\d+\]\[1] ?= ?\'(.+?)\';$",
        data,
        re.MULTILINE,
    )
    party_df = pd.DataFrame(
        zip(party_long, party_short),
        columns=["party_long", "party_short"],
    )

    answer_data = re.findall(
        r"^WOMT_aThesenParteien\[(\d+)\]\[(\d+)\] ?= ?\'(.+?)\';$",
        data,
        re.MULTILINE,
    )
    answer_df = pd.DataFrame(
        answer_data,
        columns=[
            "question",
            "party",
            "answer",
        ],
    ).astype("int")

    # can't calculate correlations if std is zero
    bad_parties = party_df.loc[answer_df.groupby("party")["answer"].std() == 0].index

    for party in bad_parties:
        answer_df = answer_df[answer_df["party"] != party]

    answer_df["party_name"] = answer_df["party"].apply(
        lambda x: party_df.loc[x, "party_short"]
    )

    pt = pd.pivot_table(
        answer_df,
        values="answer",
        index="question",
        columns="party_name",
    )

    return SurveyData(pt, question_df)


class Wom(Survery):
    def __init__(self, election: str, cacheDir: Optional[str] = None):
        super().__init__(_get_election_data(election, cacheDir))
