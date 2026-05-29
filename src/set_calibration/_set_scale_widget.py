from napari.utils.notifications import (
    show_info, 
    show_warning
)
from autooptions import OptionsWidget
from autooptions.options import Options
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import napari


class LayerScaleWidget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer"): # type: ignore
        super().__init__()
        self.viewer     = viewer
        self.sameRowSet = set()
        self.infoLabel  = QLabel("")
        self.options    = self.getOptions()
        self.operation  = None
        self.widget     = self.createLayout()
        self.viewer.layers.selection.events.changed.connect(self.onActiveLayerChanged)
        self.onActiveLayerChanged(None)

    def createLayout(self):
        widget = OptionsWidget(
            viewer=self.viewer, 
            options=self.options, 
            layout_type='vertical', 
            client=self,
            sameRowSet=self.sameRowSet
        )
        widget.addApplyButton(self.apply)
        widget.addButton("Apply to all", self.applyToAll)
        layout = QVBoxLayout()
        layout.addWidget(self.infoLabel)
        layout.addWidget(widget)
        self.setLayout(layout)
        return widget
    
    @staticmethod
    def getAxesPool():
        return [
            "YX",
            "CYX",
            "YXC",
            "ZYX",
            "ZCYX",
            "CZYX",
            "TYX",
            "TCYX",
            "CTYX",
            "TZYX",
            "TCZYX",
            "TZCYX"
        ]

    def getOptions(self):
        options = Options("SetScaleTool", "SetScaleAxes")
        options.addFloat("X", value=1.0)
        options.addFloat("Y", value=1.0)
        options.addFloat("Z", value=1.0)
        options.addChoice("Unit", choices=["pixels", "nm", "µm", "mm", "cm", "m"], value="µm")
        options.addChoice("Axes", choices=self.getAxesPool(), value='YX')
        options.load()
        self.sameRowSet = {"Y", "Z"}
        return options
    
    def updateAxesChoices(self):
        w = self.widget.widgets.get("Axes", None)
        if w is None:
            return
        _, w = w
        
        w.clear()
        l = self.viewer.layers.selection.active
        if l is None:
            w.addItems(["---"])
            return
        
        ndims = len(l.axis_labels)
        axes = [a for a in self.getAxesPool() if len(a) == ndims]
        w.addItems(axes)
    
    def _getTargetLayers(self, to_all=False):
        if to_all:
            return self.viewer.layers
        else:
            active_layer = self.viewer.layers.selection.active
            return [active_layer] if active_layer else []
        
    def onActiveLayerChanged(self, event):
        self.showCurrent()
        self.updateViewersAxisLabels()
        self.updateAxesChoices()
        
    def showCurrent(self):
        l = self.viewer.layers.selection.active
        if l is None:
            self.infoLabel.setText("")
            return
        axes = l.axis_labels
        scales = l.scale
        units = l.units
        lens = l.data.shape
        as_str =  "Axes: " + "   |   ".join(f"'{a}': {s:.2f} {u} ({l})" for a, s, u, l in zip(axes, scales, units, lens))
        self.infoLabel.setText(as_str)

    def updateViewersAxisLabels(self):
        layer = self.viewer.layers.selection.active
        if layer is None:
            return
        self.viewer.dims.axis_labels = layer.axis_labels

    def makeScalesVector(self, axes, calib):
        vec = []
        for axis in axes:
            if axis in calib:
                vec.append(calib[axis])
            else:
                vec.append(1.0)
        return vec
    
    def makeUnitsVector(self, axes, unit):
        nonSpatialAxes = {'T', 'C'}
        return [unit if axis not in nonSpatialAxes else '' for axis in axes]

    def applyToAll(self):
        self.apply(to_all=True)

    def apply(self, to_all=False):
        layers = self._getTargetLayers(to_all)
        ax = list(self.options.value("Axes"))
        u = self.options.value("Unit")
        calib = {
            'X': self.options.value("X"),
            'Y': self.options.value("Y"),
            'Z': self.options.value("Z"),
            'T': 1.0,
            'C': 1.0
        }

        vec = self.makeScalesVector(ax, calib)
        units = self.makeUnitsVector(ax, u)

        for layer in layers:
            ndims = len(layer.axis_labels)
            if len(ax) != ndims:
                show_warning(f"Layer '{layer.name}' has {ndims} dimensions, but {len(ax)} were provided.")
                continue
            layer.scale = vec
            layer.units = units
            layer.axis_labels = ax
            layer.depiction = 'volume' if 'Z' in ax else 'plane'
            layer.metadata['fr.cnrs.mri.cia.scale.unit'] = u
        
        self.updateScaleBar(u)
        self.updateViewersAxisLabels()
        self.showCurrent()
    
    def updateScaleBar(self, unit):
        self.viewer.scale_bar.unit = unit
        self.viewer.scale_bar.visible = True
