import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('episode,point_z,expected_ok', [('e',.2,True), ('other',.2,False), ('e',.1,False)])
def test_standoff_proposal_is_history_bound_and_keeps_gap(tmp_path,episode,point_z,expected_ok):
    source, current = tmp_path/'old', tmp_path/'current'
    source.mkdir(); current.mkdir()
    (source/'state.json').write_text(json.dumps(dict(observation_id='e:10',hand_pose_world=[.2,-.3,.4,1,0,0,0])))
    (current/'state.json').write_text(json.dumps(dict(observation_id=episode+':20',hand_pose_world=[.4,0,.42,1,0,0,0])))
    for directory in (source,current):
        for role in ('left','right','wrist'):
            (directory/f'{role}.png').write_bytes(b'fixture-only')
    carry = dict(observation_id='e:10',phases=[dict(hand_pose_world=[.4,0,.42,1,0,0,0])],measurements={
        'held_feature':dict(observation_id='e:10',surface_point_world_m=[.2,-.3,point_z]),
        'slot_feature':dict(observation_id='e:10',surface_point_world_m=[.4,0,0])})
    (tmp_path/'carry.json').write_text(json.dumps(carry))
    script=Path(__file__).resolve().parents[1]/'scripts/prepare_standoff_review.py'
    result=subprocess.run([sys.executable,str(script),'--capture',str(current),'--source-capture',str(source),
                           '--carry-command',str(tmp_path/'carry.json'),'--output',str(tmp_path/'out')],
                          capture_output=True,text=True)
    assert (result.returncode==0)==expected_ok
    if expected_ok:
        command=json.loads((tmp_path/'out/candidate.json').read_text())
        assert command['phases'][0]['hand_pose_world'][2]==pytest.approx(.34)
        assert command['evidence']['predicted_remaining_vertical_gap_m']==pytest.approx(.14)
        assert not command['finish']
    else:
        assert not (tmp_path/'out/candidate.json').exists()
