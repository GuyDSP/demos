import ipywidgets
import numpy as np
import pandas as pd
import plotly.graph_objs as go


def plot_recorders(recs, pplots, *args, **kwargs):

    plots = []
    for r in pplots:
        r_plots = []
        for p in r:
            x, y = p

            plot_options = dict(
                width=1800,
                height=800,
                title={
                    "text": f"CPU simulation analysis: {y}=f({x})",
                    "font": {"size": 34},
                    "x": 0.5,
                },
                xaxis={"title": {"text": f"{x}", "font": {"size": 20}}, "gridcolor": "#EBF0F8"},
                yaxis={"title": {"text": f"{y}", "font": {"size": 20}}, "gridcolor": "#EBF0F8"},
                legend={
                    "x": 0.35,
                    "y": 0.25,
                    "font": {"size": 20},
                    "orientation": "h",
                    "xanchor": "center",
                },
                plot_bgcolor="white",
                hovermode="x",
            )
            plot_options.update(kwargs)

            r_plots.append(
                go.FigureWidget(
                    data=[
                        go.Scatter(
                            x=r[x],
                            y=r[y],
                            mode="markers",
                            name=n,
                        )
                        for n, r in recs.items()
                        if x in r and y in r
                    ],
                    layout=go.Layout(**plot_options),
                )
            )
        plots.append(ipywidgets.HBox(r_plots))

    return ipywidgets.VBox(plots)
