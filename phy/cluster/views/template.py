# -*- coding: utf-8 -*-

"""Template view."""


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

import numpy as np

from phylib.utils.color import _add_selected_clusters_colors
from phylib.io.array import _index_of
from phylib.utils import emit

from phy.plot import get_linear_x
from phy.plot.visuals import PlotVisual
from .base import ManualClusteringView, ScalingMixin

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Template view
# -----------------------------------------------------------------------------

class TemplateView(ScalingMixin, ManualClusteringView):
    """This view shows all template waveforms of all clusters in a large grid of shape
    `(n_channels, n_clusters)`.

    Constructor
    -----------

    templates : function
        Maps `cluster_ids` to a list of `[Bunch(template, channel_ids)]` where `template` is
        an `(n_samples, n_channels)` array, and `channel_ids` specifies the channels of the
        `template` array (sparse format).
    channel_ids : array-like
        The list of all channel ids.
    cluster_ids : array-like
        The list of all clusters to show initially.
    cluster_color_selector : ClusterColorSelector
        The object managing the color mapping.

    """
    _default_position = 'right'
    cluster_ids = ()
    _scaling = 1.

    default_shortcuts = {
        'increase': 'ctrl+alt++',
        'decrease': 'ctrl+alt+-',
    }

    def __init__(self, templates=None, channel_ids=None, cluster_ids=None,
                 cluster_color_selector=None):
        super(TemplateView, self).__init__()
        self.state_attrs += ('scaling',)
        self.local_state_attrs += ('scaling',)

        self.cluster_color_selector = cluster_color_selector
        # Full list of channels.
        self.channel_ids = channel_ids
        # Full list of clusters.
        if cluster_ids is not None:
            self.set_cluster_ids(cluster_ids)
        # Total number of channels.
        self.n_channels = len(channel_ids)
        self.canvas.set_layout('grid', box_bounds=[[-1, -1, +1, +1]], has_clip=False)
        self.canvas.enable_axes()
        self.templates = templates

        self.visual = PlotVisual()
        self.canvas.add_visual(self.visual)
        self._cluster_box_index = {}  # dict {cluster_id: box_index} used to quickly reorder

    # Internal plot functions
    # -------------------------------------------------------------------------

    def _iter_clusters(self):
        """Iterate through all clusters in their natural order (increasing cluster id).

        Yield a tuple (cluster_rel, cluster_idx, cluster_id).

        cluster_rel : int
            Range from 0 to n_clusters - 1.
        cluster_idx : int
            The position of the current cluster in `self.cluster_ids`
        cluster_id : int
            The cluster id.

        """
        for i in range(len(self.cluster_ids)):
            yield i, self.cluster_idxs[i], self.cluster_ids_sorted[i]

    def _get_data_bounds(self, bunchs):
        m = np.median([b.template.min() for b in bunchs])
        M = np.median([b.template.max() for b in bunchs])
        return [-1, m, +1, M]

    def _plot_cluster(self, bunch):
        """Plot one cluster."""
        wave = bunch.template  # shape: (n_samples, n_channels)
        channel_ids_loc = bunch.channel_ids
        n_channels_loc = len(channel_ids_loc)

        n_samples, nc = wave.shape
        assert nc == n_channels_loc

        # Find the x coordinates.
        t = get_linear_x(n_channels_loc, n_samples)

        color = self.cluster_colors[bunch.cluster_rel]
        assert len(color) == 4

        # Generate the box index (channel_idx, cluster_idx) per vertex.
        box_index = _index_of(channel_ids_loc, self.channel_ids)
        box_index = np.repeat(box_index, n_samples)
        box_index = np.c_[
            box_index.reshape((-1, 1)),
            bunch.cluster_idx * np.ones((n_samples * n_channels_loc, 1))]
        assert box_index.shape == (n_channels_loc * n_samples, 2)
        assert box_index.size == wave.size * 2
        self._cluster_box_index[bunch.cluster_id] = box_index

        self.visual.add_batch_data(
            x=t, y=wave.T, color=color, box_index=box_index, data_bounds=self.data_bounds)

    def get_clusters_data(self, load_all=None):
        bunchs = self.templates(self.cluster_ids)
        out = []
        for cluster_rel, cluster_idx, cluster_id in self._iter_clusters():
            b = bunchs[cluster_id]
            b.cluster_rel = cluster_rel
            b.cluster_idx = cluster_idx
            b.cluster_id = cluster_id
            out.append(b)
        return out

    def _set_scaling_value(self, value):
        self._scaling = value
        self._apply_scaling()

    def _apply_scaling(self):
        sx, sy = self.canvas.layout.scaling
        self.canvas.layout.scaling = (sx, self._scaling)

    @property
    def scaling(self):
        """Return the grid scaling."""
        return self._scaling

    @scaling.setter
    def scaling(self, value):
        self._scaling = value

    # Main methods
    # -------------------------------------------------------------------------

    def set_cluster_ids(self, cluster_ids):
        self.cluster_ids = np.array(cluster_ids, dtype=np.int32)
        # Permutation of the clusters.
        self.cluster_idxs = np.argsort(self.cluster_ids)
        self.cluster_ids_sorted = self.cluster_ids[self.cluster_idxs]
        # Cluster colors, ordered by cluster id.
        self.cluster_colors = self.cluster_color_selector.get_colors(
            self.cluster_ids_sorted, alpha=.75)

    def update_cluster_sort(self, cluster_ids):
        """Update the order of the clusters."""
        if not self._cluster_box_index:  # pragma: no cover
            return self.plot()
        # Only the order of the cluster_ids is supposed to change here.
        # We just have to update box_index instead of replotting everything.
        assert len(cluster_ids) == len(self.cluster_ids)
        # Update the cluster ids, in the new order.
        self.cluster_ids = np.array(cluster_ids, dtype=np.int32)
        # Update the permutation of the clusters.
        self.cluster_idxs = np.argsort(self.cluster_ids)
        box_index = []
        for cluster_rel, cluster_idx in enumerate(self.cluster_idxs):
            cluster_id = self.cluster_ids[cluster_idx]
            clu_box_index = self._cluster_box_index[cluster_id]
            clu_box_index[:, 1] = cluster_idx
            box_index.append(clu_box_index)
        box_index = np.concatenate(box_index, axis=0)
        self.visual.set_box_index(box_index)
        self.canvas.update()

    def update_color(self, selected_clusters=None):
        """Update the color of the clusters, taking the selected clusters into account."""
        # This method is only used when the view has been plotted at least once,
        # such that self._cluster_box_index has been filled.
        if not self._cluster_box_index:
            return self.plot()
        # The call to set_cluster_ids() update the cluster_colors array.
        self.set_cluster_ids(self.cluster_ids)
        # Selected cluster colors.
        cluster_colors = self.cluster_colors
        if selected_clusters is not None:
            cluster_colors = _add_selected_clusters_colors(
                selected_clusters, self.cluster_ids_sorted, cluster_colors)
        # Number of vertices per cluster = number of vertices per signal
        n_vertices_clu = [
            len(self._cluster_box_index[cluster_id]) for cluster_id in self.cluster_ids_sorted]
        # The argument passed to set_color() must have 1 row per vertex.
        self.visual.set_color(np.repeat(cluster_colors, n_vertices_clu, axis=0))
        self.canvas.update()

    def plot(self, **kwargs):
        """Make the template plot."""

        # Retrieve the waveform data.
        bunchs = self.get_clusters_data()
        if not bunchs:
            return
        n_clusters = len(self.cluster_ids)
        self.canvas.grid.shape = (self.n_channels, n_clusters)

        self.visual.reset_batch()
        # Go through all clusters, ordered by cluster id.
        self.data_bounds = self._get_data_bounds(bunchs)
        for bunch in bunchs:
            self._plot_cluster(bunch)
        self.canvas.update_visual(self.visual)
        self._apply_scaling()
        self.canvas.axes.reset_data_bounds((0, 0, n_clusters, self.n_channels))
        self.canvas.update()

    def on_select(self, cluster_ids=(), **kwargs):
        """Update the view with the selected clusters."""
        if not cluster_ids:
            return
        self.update_color(selected_clusters=cluster_ids)

    def on_mouse_click(self, e):
        """Select a cluster by clicking on its template waveform."""
        b = e.button
        if 'Control' in e.modifiers:
            # Get mouse position in NDC.
            (channel_idx, cluster_rel), _ = self.canvas.grid.box_map(e.pos)
            cluster_id = self.cluster_ids[cluster_rel]
            logger.debug("Click on cluster %d with button %s.", cluster_id, b)
            emit('cluster_click', self, cluster_id, button=b)
