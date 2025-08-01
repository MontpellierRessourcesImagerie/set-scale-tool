import numpy as np

from set_calibration._widget import (
    LayerScaleWidget
)

def test_widget(make_napari_viewer, capsys):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    widget = LayerScaleWidget(viewer)
    viewer.add_image(np.random.random((100, 100)))
    assert True