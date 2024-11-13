"""
Example Plotly Map Panel.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|

"""

import os
import numpy as np

import fiftyone as fo
import fiftyone.core.fields as fof
import fiftyone.core.groups as fog
import fiftyone.core.labels as fol

import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone import ViewField as F


_PLOTLY_MARKER_OPACITY = 0.8
_PLOTLY_MARKER_LINE_WIDTH = 1
_PLOTLY_MARKER_SIZE_MIN = 5
_PLOTLY_MARKER_SYMBOL = "circle"
_PLOTLY_MARKER_COLORSCALE = "viridis"
_PLOTLY_GEO_SCOPE = "world"


def _get_geo_location_field(sample_collection):
    geo_schema = sample_collection.get_field_schema(
        ftype=fof.EmbeddedDocumentField, embedded_doc_type=fol.GeoLocation
    )
    if not geo_schema:
        raise ValueError("No %s field found to use" % fol.GeoLocation)

    return next(iter(geo_schema.keys()))


def _get_lat_long(sample_collection, geo_field):
    coordinate_field = f"{geo_field}.point.coordinates"
    lat = sample_collection.values(F(coordinate_field)[0])
    lng = sample_collection.values(F(coordinate_field)[1])
    return lat, lng


def _get_marker_size_list(sample_collection, marker_size_field):
    marker_size = sample_collection.values(marker_size_field)
    return marker_size


def _get_marker_color_list(sample_collection, color_field):
    color_list = sample_collection.values(color_field)
    return color_list


def _get_default_marker_sizes(n):
    marker_size = [_PLOTLY_MARKER_SIZE_MIN] * n
    return marker_size


def _get_default_color_list(n):
    colors = [1] * n
    return colors


def _get_default_hover_values(sample_collection):
    sids = sample_collection.values("id")
    return sids


def _get_hover_values(sample_collection, hover_field):
    if hover_field and hover_field.startswith("hvr_"):
        hover_field = hover_field[4:]
        hover_values = sample_collection.values(hover_field)
    else:
        hover_values = _get_default_hover_values(sample_collection)

    return hover_values


def _get_marker_size_raw(sample_collection, size_field):
    if size_field and size_field.startswith("sz_"):
        size_field = size_field[3:]
        marker_sizes_view_raw = _get_marker_size_list(sample_collection, size_field)
    else:
        # Unselected
        marker_sizes_view_raw = _get_default_marker_sizes(len(sample_collection))

    return marker_sizes_view_raw


def _get_marker_colors(sample_collection, color_field):
    if color_field and color_field.startswith("clr_"):
        color_field = color_field[4:]
        colors = _get_marker_color_list(sample_collection, color_field)
    else:
        # Unselected
        color_field = ""
        colors = _get_default_color_list(len(sample_collection))

    return colors, color_field


class PlotlyMap(foo.Panel):

    @property
    def config(self):
        return foo.PanelConfig(name="plotly_map", label="Plotly Map")

    def reset(self, ctx):
        ctx.log("reset")
        ctx.ops.clear_view()
        ctx.ops.clear_all_stages()
        ctx.ops.clear_panel_data()
        ctx.ops.clear_panel_state()
        self.on_load(ctx)

    def on_load(self, ctx, init=False):
        """
        Initial panel load. Set initial plotly trace. Initialize panel state
        """

        ctx.log("on_load")
        view = ctx.view

        geo_field = _get_geo_location_field(view)
        long, lat = _get_lat_long(view, geo_field)

        n = len(view)
        sids = view.values("id")
        hover_values = sids  # see _get_default_hover_values()
        marker_size = _get_default_marker_sizes(n)
        color_field = ""
        colors = _get_default_color_list(n)

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
                    "hoverinfo": "text",
                    "text": hover_values,
                    "marker": {
                        "size": marker_size,
                        "opacity": _PLOTLY_MARKER_OPACITY,
                        "reversescale": True,
                        "autocolorscale": False,
                        "symbol": _PLOTLY_MARKER_SYMBOL,
                        "line": {
                            "width": _PLOTLY_MARKER_LINE_WIDTH,
                        },
                        "colorscale": _PLOTLY_MARKER_COLORSCALE,
                        "cmin": 0,
                        "color": colors,
                        "colorbar": {"title": color_field},
                    },
                }
            ],
        )

        ctx.panel.state.set("slider_value", 3)
        marker_sizes_view_raw = _get_marker_size_raw(ctx.dataset, '__dne__')
        ctx.panel.state.set("marker_sizes_view_raw", marker_sizes_view_raw)
        ctx.panel.state.set("marker_sizes_all_raw_max", max(marker_sizes_view_raw))

    def on_change_dataset(self, ctx):
        ctx.log("on_change_dataset")
        self.on_load(ctx)

    def on_change_view(self, ctx):
        ctx.log("on_change_view")
        # ctx.log(f"{ctx}")
        ctx.log(f"{len(ctx.dataset)} | {len(ctx.view)}")

        # Marker sizes
        size_field = ctx.panel.get_state("size_dropdown")
        marker_sizes_view_raw = _get_marker_size_raw(ctx.view, size_field)
        ctx.panel.set_state("marker_sizes_view_raw", marker_sizes_view_raw)

        marker_sizes_all_raw_max = ctx.panel.get_state("marker_sizes_all_raw_max")
        fac = ctx.panel.get_state("slider_value")
        fac = 2*float(fac) / marker_sizes_all_raw_max
        marker_sizes = [
            max(x * fac, _PLOTLY_MARKER_SIZE_MIN) for x in marker_sizes_view_raw
        ]
        ctx.panel.set_state("map[0].marker.size", marker_sizes)

        # Marker colors
        color_field = ctx.panel.get_state("color_dropdown")
        colors, color_field = _get_marker_colors(ctx.view, color_field)
        ctx.panel.set_state("map[0].marker.color", colors)
        ctx.panel.set_state("map[0].marker.colorbar.title", color_field)

        # Hover values
        hover_field = ctx.panel.get_state("hover_dropdown")
        hover_values = _get_hover_values(ctx.view, hover_field)
        ctx.panel.set_state("map[0].text", hover_values)

        # Markers / IDs
        view = ctx.view
        geo_field = _get_geo_location_field(view)
        long, lat = _get_lat_long(view, geo_field)
        sids = view.values("id")
        ctx.panel.set_state("map[0].lon", long)
        ctx.panel.set_state("map[0].lat", lat)
        ctx.panel.set_state("map[0].ids", sids)

    def render(self, ctx):
        ctx.log("render")
        panel = types.Object()

        dataset = ctx.dataset
        numeric_fields = dataset.get_field_schema([fo.FloatField, fo.IntField]).keys()

        dropdown = types.DropdownView()
        dropdown.add_choice("__unk__", label="<select>")
        for num_field in numeric_fields:
            dropdown.add_choice(
                f"sz_{num_field}",
                label=num_field,
            )
        panel.str(
            "size_dropdown",
            view=dropdown,
            label="Marker Size Field",
            on_change=self.on_change_marker_size_field,
        )

        dropdown = types.DropdownView()
        dropdown.add_choice("__unk__", label="<select>")
        for num_field in numeric_fields:
            dropdown.add_choice(
                f"clr_{num_field}",
                label=num_field,
            )
        panel.str(
            "color_dropdown",
            view=dropdown,
            label="Color Size Field",
            on_change=self.on_change_marker_color_field,
        )

        # Slider
        # Slider Val is log10(pixel_size)
        schema = {"min": 1, "max": 10 }
        slider = types.SliderView(
            data=ctx.panel.state.slider_value, label="Marker Size"
        )
        panel.int(
            "slider_value", view=slider, on_change=self.slider_change_value, **schema
        )

        # Hover values
        fields = dataset.get_field_schema([fo.StringField]).keys()
        dropdown = types.DropdownView()
        dropdown.add_choice("__unk__", label="<select>")
        for field in fields:
            dropdown.add_choice(
                f"hvr_{field}",
                label=field,
            )
        panel.str(
            "hover_dropdown",
            view=dropdown,
            label="Hover Text Field",
            on_change=self.on_change_hover_text_field,
        )

        panel.plot(
            "map",
            layout={"geo": {"scope": _PLOTLY_GEO_SCOPE}},
            on_selected=self.on_plot_selected,
            on_double_click=self.on_plot_double_click,
        )

        return types.Property(panel, view=types.GridView())

    def on_change_hover_text_field(self, ctx):
        hover_field = ctx.params["value"]
        hover_values = _get_hover_values(ctx.view, hover_field)
        ctx.panel.set_state("map[0].text", hover_values)

    def on_change_marker_size_field(self, ctx):
        size_field = ctx.params["value"]
        marker_sizes_view_raw = _get_marker_size_raw(ctx.view, size_field)
        ctx.panel.set_state("marker_sizes_view_raw", marker_sizes_view_raw)

        marker_sizes_all = _get_marker_size_raw(ctx.dataset, size_field)
        marker_sizes_all_raw_max = max(marker_sizes_all)
        ctx.panel.set_state("marker_sizes_all_raw_max", marker_sizes_all_raw_max)

        fac = ctx.panel.get_state("slider_value")
        fac = 2*float(fac) / marker_sizes_all_raw_max
        marker_sizes = [
            max(x * fac, _PLOTLY_MARKER_SIZE_MIN) for x in marker_sizes_view_raw
        ]
        ctx.panel.set_state("map[0].marker.size", marker_sizes)

    def on_change_marker_color_field(self, ctx):
        color_field = ctx.params["value"]
        colors, color_field = _get_marker_colors(ctx.view, color_field)
        ctx.panel.set_state("map[0].marker.color", colors)
        ctx.panel.set_state("map[0].marker.colorbar.title", color_field)

    def slider_change_value(self, ctx):
        marker_sizes_view_raw = ctx.panel.get_state("marker_sizes_view_raw")
        marker_sizes_all_raw_max = ctx.panel.get_state("marker_sizes_all_raw_max")

        fac = ctx.params["value"]
        fac = 2*float(fac) / marker_sizes_all_raw_max
        marker_sizes = [
            max(x * fac, _PLOTLY_MARKER_SIZE_MIN) for x in marker_sizes_view_raw
        ]
        ctx.panel.set_state("map[0].marker.size", marker_sizes)

    def on_change_ctx(self, ctx):
        ctx.log("on_change_ctx")

    def on_plot_double_click(self, ctx):
        ctx.ops.clear_view()
        ctx.ops.clear_all_stages()
        self.on_change_view(ctx)

    def on_plot_selected(self, ctx):
        selected_points = ctx.params.get("data", [])
        selected_sample_ids = [d.get("id", None) for d in selected_points]
        if len(selected_sample_ids) > 0:
            ctx.ops.set_extended_selection(selected_sample_ids)


def register(p):
    p.register(PlotlyMap)
