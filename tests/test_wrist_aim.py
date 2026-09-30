import pytest
from pathlib import Path
from physical_exec.config import configured_camera_view


def test_wrist_aim_is_opt_in_and_does_not_mutate_source():
    view = {'link':'panda_hand','eye':[.0465,-.02,.036],'target':[.0465,-.02,.3],'focal':10.5}
    task = {'camera_map':{'wrist':'wrist'}}
    assert configured_camera_view(task,'wrist',view) is view
    task['wrist_target_hand'] = [0,0,.1034]
    changed = configured_camera_view(task,'wrist',view)
    assert changed['target'] == [0,0,.1034]
    assert view['target'] == [.0465,-.02,.3]
    assert changed['eye'] == view['eye'] and changed['focal'] == 10.5
    assert configured_camera_view(task,'external_right',view) is view
    with pytest.raises(ValueError):
        configured_camera_view(task,'wrist',{'link':'wrong'})


def test_ram_aimed_condition_changes_only_robot_local_view_and_notes():
    from physical_exec.config import load_task
    root = Path(__file__).resolve().parents[1]/'configs/tasks'
    baseline, old_limits = load_task(root/'pc_ram.json')
    aimed, new_limits = load_task(root/'pc_ram_wrist_aim.json')
    assert {k for k in aimed if aimed[k] != baseline.get(k)} == {'wrist_target_hand','notes'}
    assert aimed['wrist_target_hand'] == [0,0,.1034]
    assert old_limits == new_limits
