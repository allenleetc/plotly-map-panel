# Plotly Map Panel

An example map panel using PlotlyView. 

This example demonstrates mapping functionality built on PlotlyView
as an alternative to fiftyone's built-in 
[Map Panel](https://docs.voxel51.com/user_guide/app.html#map-panel) 
that relies on [Mapbox](https://www.mapbox.com/). 

## Installation

```shellx
fiftyone plugins download https://github.com/allenleetc/plotly-map-panel
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Usage

[Install fiftyone](https://docs.voxel51.com/getting_started/install.html#fiftyone-installation)
and then run the following code to create a test dataset.

```py
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset('https://github.com/allenleetc/world-airports',
                               dataset_name='world-airports',
                               persistent=True)
                               
session = fo.launch_app(dataset,auto=False)
```

2.  Press the `+` button next to the "Samples" tab

3.  Select the `Plotly Map` panel

4.  Select dataset fields in the pulldown menus and explore the dataset!
