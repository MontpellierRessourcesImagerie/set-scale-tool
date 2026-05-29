from napari.utils.notifications import (
    show_info, 
    show_warning
)
from autooptions import OptionsWidget
from autooptions.options import Options
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import napari

from napari.layers.labels.labels import Labels
from napari.layers.image.image import Image

class SplitChannelsWidget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer"): # type: ignore
        super().__init__()
        self.viewer     = viewer
        self.sameRowSet = set()
        self.options    = self.getOptions()
        self.operation  = None
        self.widget     = self.createLayout()

    def createLayout(self):
        widget = OptionsWidget(
            viewer=self.viewer, 
            options=self.options, 
            layout_type='vertical', 
            client=self,
            sameRowSet=self.sameRowSet
        )
        widget.addApplyButton(self.apply)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        self.setLayout(layout)
        return widget

    def getOptions(self):
        options = Options("SetScaleTool", "SplitChannels")
        options.addBool("Remove original?", value=True)
        options.addBool("Apply to all", value=True)
        options.load()
        return options
    
    def _getTargetLayers(self):
        if self.options.value("Apply to all"):
            return list(self.viewer.layers)
        else:
            active_layer = self.viewer.layers.selection
            return [active_layer] if active_layer else []
    
    def removeAxis(self, v, index):
        vector = list(v)
        return vector[:index] + vector[index+1:]

    def splitChannels(self, layer):
        if 'C' not in layer.axis_labels:
            show_info(f"'{layer.name}' does not have a 'C' axis.")
            return False
        
        c_axis = layer.axis_labels.index('C')
        data = layer.data
        metadata = layer.metadata
        name = layer.name

        scale = self.removeAxis(layer.scale, c_axis)
        units = self.removeAxis(layer.units, c_axis)
        translate = self.removeAxis(layer.translate, c_axis)
        axis_labels = self.removeAxis(layer.axis_labels, c_axis)
        depiction = 'volume' if 'Z' in layer.axis_labels else 'plane'

        self.viewer.add_image(
            data=data,
            scale=scale,
            units=units,
            metadata=metadata,
            translate=translate,
            name=name,
            channel_axis=c_axis,
            blending='additive',
            axis_labels=axis_labels,
            depiction=depiction
        )
        
        return True
    
    def removeLayers(self, layer_names):
        for name in layer_names:
            if name in self.viewer.layers:
                l = self.viewer.layers[name]
                self.viewer.layers.remove(l)
    
    def apply(self):
        layers = self._getTargetLayers()
        toBeRemoved = set()
        for layer in layers:
            if type(layer) not in [Image, Labels]:
                continue
            if self.splitChannels(layer):
                toBeRemoved.add(layer.name)
        self.removeLayers(toBeRemoved)
