
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._set_scale_widget import LayerScaleWidget
from ._split_channels_widget import SplitChannelsWidget

__all__ = (
    "LayerScaleWidget",
    "SplitChannelsWidget"
)
