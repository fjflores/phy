# -*- coding: utf-8 -*-

"""Test GUI component."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import yield_fixture, fixture
import numpy as np
from numpy.testing import assert_array_equal as ae

from .. import supervisor as _supervisor
from ..supervisor import (Supervisor,
                          ActionFlow,
                          ClusterView,
                          SimilarityView,
                          ActionCreator,
                          )
from phy.io import Context
from phy.gui import GUI
from phy.gui.qt import qInstallMessageHandler
from phy.gui.tests.test_qt import _block
from phy.gui.tests.test_widgets import _assert, _wait_until_table_ready


def handler(msg_type, msg_log_context, msg_string):
    pass


qInstallMessageHandler(handler)


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@yield_fixture
def gui(tempdir, qtbot):
    # NOTE: mock patch show box exec_
    _supervisor._show_box = lambda _: _

    gui = GUI(position=(200, 100), size=(500, 500), config_dir=tempdir)
    gui.show()
    qtbot.waitForWindowShown(gui)
    yield gui
    qtbot.wait(5)
    gui.close()
    del gui
    qtbot.wait(5)


@fixture
def supervisor(qtbot, gui, cluster_ids, cluster_groups,
               quality, similarity,
               tempdir):
    spike_clusters = np.array(cluster_ids)

    mc = Supervisor(spike_clusters,
                    cluster_groups=cluster_groups,
                    quality=quality,
                    similarity=similarity,
                    context=Context(tempdir),
                    )
    mc.attach(gui)
    _wait_until_table_ready(qtbot, mc.cluster_view)
    #_wait_until_table_ready(qtbot, mc.similarity_view)
    return mc


#------------------------------------------------------------------------------
# Test action flow
#------------------------------------------------------------------------------

def test_action_flow_1():
    assert ActionFlow()._previous_state(None) is None


def test_action_flow_2():
    af = ActionFlow()
    af.update_current_state(cluster_ids=[0])
    assert af.current().cluster_ids == [0]


def test_action_flow_3():
    af = ActionFlow()

    af.add_state(cluster_ids=[0], similar=[100], next_similar=101)
    assert af.current().next_cluster is None

    af.update_current_state(next_cluster=1000)
    assert af.current().next_cluster == 1000

    af.update_current_state(cluster_ids=[1])
    assert af.current().cluster_ids == [0]


def test_action_flow_merge():
    af = ActionFlow()
    af.add_state(cluster_ids=[0], similar=[100], next_cluster=2, next_similar=101)
    af.add_merge(cluster_ids=[0, 100], to=1000)

    s = af.current()
    assert s.type == 'state'
    assert s.cluster_ids == [1000]
    assert s.similar == [101]

    af.add_undo()
    su = af.current()
    assert su.type == 'state'
    assert su.cluster_ids == [0]
    assert su.similar == [100]
    assert su.next_cluster == 2
    assert su.next_similar == 101

    af.add_redo()
    assert af.current() == s


def test_action_flow_split():
    af = ActionFlow()
    af.add_state(cluster_ids=[0], similar=[100], next_cluster=2, next_similar=101)
    af.add_split(old_cluster_ids=[0, 100], new_cluster_ids=[1000, 1001])

    s = af.current()
    assert s.type == 'state'
    assert s.cluster_ids == [1000, 1001]
    assert s.similar == []


def test_action_flow_move_clusters_1():
    af = ActionFlow()
    af.add_state(cluster_ids=[0], similar=[100], next_cluster=2, next_similar=101)
    af.add_move(cluster_ids=[0], group='good')

    s = af.current()
    assert s.type == 'state'
    assert s.cluster_ids == [2]
    # No connection to request_next_similar, so no next similar cluster.
    assert s.similar == []


def test_action_flow_move_clusters_2():
    af = ActionFlow()

    @af.connect
    def on_request_next_similar(cluster_id):
        return 1234

    af.add_state(cluster_ids=[0], similar=[100], next_cluster=2, next_similar=101)
    af.add_move(cluster_ids=[0], group='good')

    s = af.current()
    assert s.type == 'state'
    assert s.cluster_ids == [2]
    assert s.similar == [1234]


def test_action_flow_move_similar():
    af = ActionFlow()
    af.add_state(cluster_ids=[0], similar=[100], next_cluster=2, next_similar=101)
    af.add_move(cluster_ids=[100], group='good')

    s = af.current()
    assert s.type == 'state'
    assert s.cluster_ids == [0]
    assert s.similar == [101]


#------------------------------------------------------------------------------
# Test cluster and similarity views
#------------------------------------------------------------------------------

def test_cluster_view_1(qtbot, gui):
    data = [{"id": i,
             "n_spikes": 100 - 10 * i,
             "group": {2: 'noise', 3: 'noise', 5: 'mua', 8: 'good'}.get(i, None),
             "is_masked": i in (2, 3, 5),
             } for i in range(10)]
    cv = ClusterView(data)
    _wait_until_table_ready(qtbot, cv)

    cv.sort_by('n_spikes', 'asc')
    _assert(cv.get_state, {'current_sort': ('n_spikes', 'asc')})

    cv.set_state({'current_sort': ('id', 'desc')})
    _assert(cv.get_state, {'current_sort': ('id', 'desc')})


def test_similarity_view_1(qtbot, gui):
    data = [{"id": i,
             "n_spikes": 100 - 10 * i,
             "group": {2: 'noise', 3: 'noise', 5: 'mua', 8: 'good'}.get(i, None),
             } for i in range(10)]
    sv = SimilarityView(data)
    _wait_until_table_ready(qtbot, sv)

    @sv.connect_
    def on_request_similar_clusters(cluster_id):
        return [{'id': id} for id in (100 + cluster_id, 110 + cluster_id, 102 + cluster_id)]

    sv.reset(5)
    _assert(sv.get_ids, [105, 115, 107])


#------------------------------------------------------------------------------
# Test ActionCreator
#------------------------------------------------------------------------------

def test_action_creator_1(qtbot, gui):
    ac = ActionCreator()
    ac.attach(gui)
    gui.show()
    # qtbot.stop()


#------------------------------------------------------------------------------
# Test GUI component
#------------------------------------------------------------------------------

def _assert_selected(supervisor, sel):
    cluster_ids = []
    similar = []
    supervisor.cluster_view.get_selected(lambda c: cluster_ids.append(c))
    _block(lambda: len(cluster_ids) > 0 and len(cluster_ids[0]) > 0)
    supervisor.similarity_view.get_selected(lambda s: similar.append(s))
    _block(lambda: len(similar) > 0)
    assert cluster_ids[0] + similar[0] == sel


def test_supervisor_select(qtbot, supervisor):
    supervisor.cluster_view.select([0])
    _assert_selected(supervisor, [0])


def test_supervisor_order(qtbot, supervisor):
    supervisor.select([1, 0])
    _assert_selected(supervisor, [1, 0])


def test_supervisor_edge_cases(supervisor):

    # Empty selection at first.
    ae(supervisor.clustering.cluster_ids, [0, 1, 2, 10, 11, 20, 30])

    supervisor.select([0])
    _assert_selected(supervisor, [0])

    supervisor.undo()
    supervisor.redo()

    # Merge.
    supervisor.merge()
    _assert_selected(supervisor, [0])

    supervisor.merge([])
    _assert_selected(supervisor, [0])

    supervisor.merge([10])
    _assert_selected(supervisor, [0])

    # Split.
    supervisor.split([])
    _assert_selected(supervisor, [0])

    # Move.
    supervisor.move('ignored', [])

    supervisor.save()


def test_supervisor_skip(qtbot, gui, supervisor):

    # yield [0, 1, 2, 10, 11, 20, 30]
    # #      i, g, N,  i,  g,  N, N
    expected = [30, 20, 11, 2, 1]

    for clu in expected:
        supervisor.cluster_view.next()
        _assert_selected(supervisor, [clu])


def test_supervisor_merge(supervisor):

    supervisor.cluster_view.select([30])
    supervisor.similarity_view.select([20])
    _assert_selected(supervisor, [30, 20])

    supervisor.merge()
    _assert_selected(supervisor, [31, 11])

    supervisor.undo()
    _assert_selected(supervisor, [30, 20])

    supervisor.redo()
    _assert_selected(supervisor, [31, 11])


def test_supervisor_merge_move(supervisor):
    """Check that merge then move selects the next cluster in the original
    cluster view, not the updated cluster view."""

    supervisor.cluster_view.select([20, 11])

    supervisor.merge()
    _assert_selected(supervisor, [31])

    supervisor.move('good')
    _assert_selected(supervisor, [2])

    supervisor.cluster_view.select([30])

    supervisor.move('good')
    _assert_selected(supervisor, [2])


def test_supervisor_split_0(supervisor):

    supervisor.select([1, 2])
    supervisor.split([1, 2])
    _assert_selected(supervisor, [31])

    supervisor.undo()
    _assert_selected(supervisor, [1, 2])

    supervisor.redo()
    _assert_selected(supervisor, [31])


def test_supervisor_split_1(gui, supervisor):

    supervisor.select([1, 2])

    @gui.connect_
    def on_request_split():
        return supervisor.clustering.spikes_in_clusters([1, 2])

    supervisor.split()
    _assert_selected(supervisor, [31])


def test_supervisor_split_2(gui, quality, similarity):
    spike_clusters = np.array([0, 0, 1])

    supervisor = Supervisor(spike_clusters,
                            similarity=similarity,
                            )
    supervisor.attach(gui)

    supervisor.add_column(quality, name='quality', default=True)
    supervisor.set_default_sort('quality', 'desc')

    supervisor.split([0])
    _assert_selected(supervisor, [3, 2])


def test_supervisor_state(tempdir, qtbot, gui, supervisor):

    cv = supervisor.cluster_view
    cv.sort_by('id')
    gui.close()
    assert cv.state['sort_by'] == ('id', 'asc')
    cv.set_state(cv.state)
    assert cv.state['sort_by'] == ('id', 'asc')


def test_supervisor_label(supervisor):

    supervisor.select([20])
    supervisor.label("my_field", 3.14)

    supervisor.save()

    assert 'my_field' in supervisor.fields
    assert supervisor.get_labels('my_field')[20] == 3.14


def test_supervisor_move_1(supervisor):

    supervisor.select([20])
    _assert_selected(supervisor, [20])

    assert not supervisor.move('', '')

    supervisor.move('noise')
    _assert_selected(supervisor, [11])

    supervisor.undo()
    _assert_selected(supervisor, [20])

    supervisor.redo()
    _assert_selected(supervisor, [11])


def test_supervisor_move_2(supervisor):

    supervisor.select([20])
    supervisor.similarity_view.select([10])

    _assert_selected(supervisor, [20, 10])

    supervisor.move('noise', 10)
    _assert_selected(supervisor, [20, 2])

    supervisor.undo()
    _assert_selected(supervisor, [20, 10])

    supervisor.redo()
    _assert_selected(supervisor, [20, 2])


#------------------------------------------------------------------------------
# Test shortcuts
#------------------------------------------------------------------------------

def test_supervisor_action_reset(qtbot, supervisor):

    supervisor.actions.select([10, 11])

    supervisor.actions.reset()
    _assert_selected(supervisor, [30])

    supervisor.actions.next()
    _assert_selected(supervisor, [30, 20])

    supervisor.actions.next()
    _assert_selected(supervisor, [30, 11])

    supervisor.actions.previous()
    _assert_selected(supervisor, [30, 20])


def test_supervisor_action_nav(qtbot, supervisor):

    supervisor.actions.reset()
    _assert_selected(supervisor, [30])

    supervisor.actions.next_best()
    _assert_selected(supervisor, [20])

    supervisor.actions.previous_best()
    _assert_selected(supervisor, [30])


def test_supervisor_action_move_1(qtbot, supervisor):

    supervisor.actions.next()

    _assert_selected(supervisor, [30])
    supervisor.actions.move_best_to_noise()

    _assert_selected(supervisor, [20])
    supervisor.actions.move_best_to_mua()

    _assert_selected(supervisor, [11])
    supervisor.actions.move_best_to_good()

    _assert_selected(supervisor, [2])

    supervisor.cluster_meta.get('group', 30) == 'noise'
    supervisor.cluster_meta.get('group', 20) == 'mua'
    supervisor.cluster_meta.get('group', 11) == 'good'

    # qtbot.stop()


def test_supervisor_action_move_2(supervisor):

    supervisor.select([30])
    supervisor.similarity_view.select([20])

    _assert_selected(supervisor, [30, 20])
    supervisor.actions.move_similar_to_noise()

    _assert_selected(supervisor, [30, 11])
    supervisor.actions.move_similar_to_mua()

    _assert_selected(supervisor, [30, 2])
    supervisor.actions.move_similar_to_good()

    _assert_selected(supervisor, [30, 1])

    supervisor.cluster_meta.get('group', 20) == 'noise'
    supervisor.cluster_meta.get('group', 11) == 'mua'
    supervisor.cluster_meta.get('group', 2) == 'good'


def test_supervisor_action_move_3(supervisor):

    supervisor.select([30])
    supervisor.similarity_view.select([20])

    _assert_selected(supervisor, [30, 20])
    supervisor.actions.move_all_to_noise()
    supervisor.next()

    _assert_selected(supervisor, [11, 2])
    supervisor.actions.move_all_to_mua()

    _assert_selected(supervisor, [1])
    supervisor.actions.move_all_to_good()

    _assert_selected(supervisor, [1])

    supervisor.cluster_meta.get('group', 30) == 'noise'
    supervisor.cluster_meta.get('group', 20) == 'noise'

    supervisor.cluster_meta.get('group', 11) == 'mua'
    supervisor.cluster_meta.get('group', 10) == 'mua'

    supervisor.cluster_meta.get('group', 2) == 'good'
    supervisor.cluster_meta.get('group', 1) == 'good'
