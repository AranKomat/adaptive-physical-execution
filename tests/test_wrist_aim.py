import pytest
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
