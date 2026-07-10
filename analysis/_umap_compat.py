"""
analysis/_umap_compat.py
------------------------
UMAP import compatibility shim.

umap/__init__.py unconditionally does:
    from .parametric_umap import ParametricUMAP

parametric_umap.py requires TensorFlow + Keras at CLASS DEFINITION time
(line 62: tf.keras.losses.BinaryCrossentropy()), so it crashes when
TensorFlow is absent or not fully initialised.

Fix: pre-register a stub module in sys.modules under the key
'umap.parametric_umap' BEFORE 'import umap' runs.  Python's import
machinery checks sys.modules first, so the file is never loaded.

Usage in other modules:
    from analysis._umap_compat import UMAP
"""
import sys
import types

# Pre-register stub BEFORE importing umap to block parametric_umap.py
if "umap.parametric_umap" not in sys.modules:
    _stub = types.ModuleType("umap.parametric_umap")
    _stub.ParametricUMAP = None  # type: ignore[attr-defined]
    sys.modules["umap.parametric_umap"] = _stub

from umap import UMAP  # noqa: E402  # type: ignore[import-untyped]

__all__ = ["UMAP"]
