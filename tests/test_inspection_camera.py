import numpy as np
import pytest
from physical_exec.inspection_camera import camera_path

HAND = [.3,-.3,.45,0,0,1,0]

def test_bounded_continuous_camera_path():
    path = camera_path([.45,.5,1.4],[.85,.3,1.05],HAND,HAND,288,1/48)
    np.testing.assert_allclose(path[-1],[.85,.3,1.05])
    assert np.max(np.linalg.norm(np.diff(path,axis=0),axis=1))*48 <= .12

@pytest.mark.parametrize('eye,hand,actions', [
    ([.85,.3,.7], HAND, 288),
    ([.85,.3,1.05], [.4,-.3,.45,0,0,1,0], 288),
    ([.85,.3,1.05], HAND, 10),
    ([float('nan'),.3,1.05], HAND, 288),
])
def test_reject_unbounded_camera_commands(eye,hand,actions):
    with pytest.raises(ValueError):
        camera_path([.45,.5,1.4],eye,HAND,hand,actions,1/48)
