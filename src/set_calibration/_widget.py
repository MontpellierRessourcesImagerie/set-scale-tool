from typing import TYPE_CHECKING

from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget
from skimage.util import img_as_float
import numpy as np

if TYPE_CHECKING:
    import napari


class LayerScaleWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.setLayout(QVBoxLayout())

        # Labels and line edits for scale
        self.active_layer_name = QLabel("- No active layer -")
        self.layout().addWidget(self.active_layer_name)

        self.scale_x_input = QLineEdit()
        self.scale_y_input = QLineEdit()
        self.scale_z_input = QLineEdit()
        self.unit_input = QLineEdit()

        self.label_x = QLabel("Scale X:")
        self.label_y = QLabel("Scale Y:")
        self.label_z = QLabel("Scale Z:")
        self.label_unit = QLabel("Unit:")

        self.x_line = QHBoxLayout()
        self.y_line = QHBoxLayout()
        self.z_line = QHBoxLayout()
        self.unit_line = QHBoxLayout()

        # Add widgets to layout
        self.x_line.addWidget(self.label_x)
        self.x_line.addWidget(self.scale_x_input)
        self.y_line.addWidget(self.label_y)
        self.y_line.addWidget(self.scale_y_input)
        self.z_line.addWidget(self.label_z)
        self.z_line.addWidget(self.scale_z_input)
        self.unit_line.addWidget(self.label_unit)
        self.unit_line.addWidget(self.unit_input)

        self.all_inputs = QVBoxLayout()

        self.all_inputs.addLayout(self.x_line)
        self.all_inputs.addLayout(self.y_line)
        self.all_inputs.addLayout(self.z_line)
        self.all_inputs.addLayout(self.unit_line)

        # Buttons
        # "Apply" -> Just to active
        # "Apply to all" -> Apply to all selected layers.
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_scale)
        self.apply_to_selection_button = QPushButton("Apply to all")
        self.apply_to_selection_button.clicked.connect(self.apply_scale_to_selection)

        self.all_inputs.addWidget(self.apply_button)
        self.all_inputs.addWidget(self.apply_to_selection_button)

        self.layout().addLayout(self.all_inputs)

        self.viewer.layers.selection.events.active.connect(self.update_active_layer)
        self.update_active_layer()

    def update_active_layer(self, event=None):
        layer = self.viewer.layers.selection.active
        if layer is None:
            self.active_layer_name.setText("- No active layer -")
            self.set_input_visibility(False)
            self.viewer.scale_bar.visible = False
        else:
            self.active_layer_name.setText(layer.name)
            self.set_input_visibility(True)
            scale = layer.scale
            self.scale_x_input.setText(str(scale[-1]))
            self.scale_y_input.setText(str(scale[-2]))

            # Check for 3D and 3D+t layers
            if layer.ndim >= 3:
                self.scale_z_input.setText(str(scale[-3]))
                self.scale_z_input.setVisible(True)
                self.label_z.setVisible(True)
            else:
                self.scale_z_input.setVisible(False)
                self.label_z.setVisible(False)

            unit = layer.metadata.get('fr.cnrs.mri.cia.scale.unit', 'pixel')
            self.unit_input.setText(unit)
            self.update_scale_bar(layer)

    def set_input_visibility(self, visible):
        self.scale_x_input.setVisible(visible)
        self.scale_y_input.setVisible(visible)
        self.scale_z_input.setVisible(visible)
        self.unit_input.setVisible(visible)

        self.label_x.setVisible(visible)
        self.label_y.setVisible(visible)
        self.label_z.setVisible(visible)
        self.label_unit.setVisible(visible)

        self.apply_button.setVisible(visible)
        self.apply_to_selection_button.setVisible(visible)

    def update_scale_bar(self, layer):
        self.viewer.scale_bar.unit = self.unit_input.text()
        self.viewer.scale_bar.visible = True

    def apply_scale(self):
        self._set_layer_scale(self.viewer.layers.selection.active)

    def apply_scale_to_selection(self):
        for layer in self.viewer.layers:
            self._set_layer_scale(layer)

    def _set_layer_scale(self, layer):
        if layer:
            scale_x = float(self.scale_x_input.text())
            scale_y = float(self.scale_y_input.text())
            scale = np.ones(layer.ndim)
            scale[-1] = scale_x
            scale[-2] = scale_y

            if self.scale_z_input.isVisible():
                scale_z = float(self.scale_z_input.text())
                scale[-3] = scale_z

            layer.scale = scale
            unit = self.unit_input.text()
            layer.metadata['fr.cnrs.mri.cia.scale.unit'] = unit
            self.update_scale_bar(layer)

