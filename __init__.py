"""
Example Plotly Map Panel.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import os

import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone import ViewField as F


class PlotlyMap(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(name="plotly_map", label="Plotly Map")

    def reset(self, ctx):
        ctx.ops.clear_view()
        ctx.ops.clear_all_stages()
        ctx.ops.clear_panel_data()
        ctx.ops.clear_panel_state()

        self.on_load(ctx)

    def on_load(self, ctx):

        view = ctx.view
        long, lat = view.values(["long", "lat"])
        airports = view.values("airport")
        count = view.values("cnt")
        sids = view.values("id")

        ctx.panel.state.set(
            "map",
            [
                {
                    "type": "scattergeo",
                    "locationmode": "USA-states",
                    "lon": long,
                    "lat": lat,
                    "ids": sids,
                    "mode": "markers",
                    "hoverinfor": airports,
                    "text": airports,
                    "marker": {
                        "size": 8,
                        "opacity": 0.8,
                        "reversescale": True,
                        "autocolorscale": False,
                        "symbol": "square",
                        "line": {
                            "width": 1,
                        },
                        "colorscale": "viridis",
                        "cmin": 0,
                        "color": count,
                        "colorbar": {"title": "Incoming Flights February 2011"},
                    },
                }
            ],
        )

    def render(self, ctx):
        panel = types.Object()

        # Define components that appear in the panel's main body
        panel.str("event", label="The last event", view=types.LabelValueView())
        panel.obj("event_data", label="The last event data", view=types.JSONView())

        panel.plot(
            "map",
            layout={"geo": {"scope": "usa"}},
            width="800px",
            on_selected=self.on_selected_embeddings,  # custom event callback
            on_double_click=self.on_double_click,
        )

        return types.Property(panel, view=types.GridView())

    def on_change_view(self, ctx):
        event = {
            "data": ctx.view._serialize(),
            "count": len(ctx.view),
            "description": "the current view",
        }
        ctx.panel.set_state("event", "on_change_view")
        ctx.panel.set_data("event_data", event)

        self.on_load(ctx)

    def on_double_click(self, ctx):
        self.reset(ctx)

    def on_selected_embeddings(self, ctx):

        selected_points = ctx.params.get("data", [])
        selected_sample_ids = [d.get("id", None) for d in selected_points]

        event = {
            "data": selected_points,
            "count": len(selected_points),
            "description": "selected pts",
        }
        ctx.panel.set_state("event", "on_selected_embs")
        ctx.panel.set_data("event_data", event)

        if len(selected_sample_ids) > 0:
            ctx.ops.set_extended_selection(selected_sample_ids)


def register(p):
    p.register(PlotlyMap)
