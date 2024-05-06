import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("agg")

from matplotlib.figure import Figure
from matplotlib.axes import Axes

import pandas as pd
import seaborn as sns

sns.set_style("darkgrid")

from sklearn.decomposition import PCA
from sklearn.cluster import AffinityPropagation

from dataclasses import dataclass
from typing import Optional


@dataclass
class SurveyData:
    answer_table: pd.DataFrame
    questions: pd.DataFrame


@dataclass
class PcaPlots:
    scatter: Figure
    component_0: Figure
    component_1: Figure


class Survery:
    data: SurveyData

    def __init__(self, data: SurveyData):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        plt.close("all")

    def plot_clustermap(self, answers: Optional[list[int]] = None) -> Figure:
        table = self.data.answer_table
        if answers is not None and len(answers) == len(table.index):
            table["You"] = answers

        annotations = table.corr().apply(
            lambda s: pd.Series([f"{int(100*x)}" if x != 1 else "" for x in s])
        )

        sns.clustermap(
            table.corr(),
            cmap="RdYlGn",
            center=0,
            annot=annotations,
            fmt="",
            figsize=(12, 12),
        )
        return plt.gcf()

    def plot_pca(self, answers: Optional[list[int]] = None) -> PcaPlots:
        table = self.data.answer_table
        if answers is not None and len(answers) == len(table.index):
            table["You"] = answers
        table = table.T

        pca = PCA(2)
        cluster = AffinityPropagation()

        party_pca = pd.DataFrame(
            pca.fit_transform(table),
            columns=["pca_0", "pca_1"],
            index=table.index,
        )
        party_pca["cluster"] = cluster.fit_predict(party_pca)

        scatter = plt.figure(figsize=(12, 10))
        ax: Axes
        ax = scatter.add_subplot()
        sns.scatterplot(
            data=party_pca,
            x="pca_0",
            y="pca_1",
            hue="cluster",
            ax=ax,
            palette="tab10",
        )
        ax.set_aspect("equal")

        for line in party_pca.index:
            ax.text(
                party_pca.loc[line, "pca_0"] + 0.05,  # type: ignore
                party_pca.loc[line, "pca_1"] + 0.05,  # type: ignore
                line,
            )

        components = self.data.questions.join(
            pd.DataFrame(pca.components_.T, columns=["pca_0", "pca_1"])
        )

        component_0 = plt.figure(figsize=(8, 12))
        sns.barplot(data=components, x="pca_0", y="title", orient="h")
        plt.tight_layout()

        component_1 = plt.figure(figsize=(8, 12))
        sns.barplot(data=components, x="pca_1", y="title", orient="h")
        plt.tight_layout()

        return PcaPlots(scatter, component_0, component_1)
