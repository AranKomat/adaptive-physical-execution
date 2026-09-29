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
        assert command['execution_backend']=='local_stage_continuous'
        assert command['phases'][0]['actions']==128
    else:
        assert not (tmp_path/'out/candidate.json').exists()


def test_reviewed_standoff_preserves_guard_and_compiled_budget():
    from physical_exec.carry import reviewed_standoff_stages
    hand=[.4,0,.42,1,0,0,0]
    plan=dict(observation_id='e:20',finish=False,execution_backend='local_stage_continuous',
              target_source='historical depth, rigid grasp assumption',
              phases=[dict(name='bounded_closer_standoff',hand_pose_world=[.4,0,.34,1,0,0,0],
                           finger_position_m=.012,actions=128)],
              evidence=dict(observation_id='e:20',proposed_descent_m=.08,
                            predicted_remaining_vertical_gap_m=.14))
    review=dict(observation_id='e:20',decision='approve_standoff')
    stages=reviewed_standoff_stages(plan,review,'e:20',hand,.30000001192092896,1/15)
    assert [s['settle_at_end'] for s in stages]==[False,True]
    assert sum(s['max_steps'] for s in stages)==128
    assert all(s['contact_tracking_guard'] and s['gripper_open']==.30000001192092896 for s in stages)
    assert stages[-1]['hand_pose_world']==pytest.approx(plan['phases'][0]['hand_pose_world'])
    import copy
    for change in ('old_budget','stale_review','refused','gap','lateral','grip','cadence'):
        p,r=copy.deepcopy(plan),dict(review)
        dt=1/15
        if change=='old_budget': p['phases'][0]['actions']=90
        if change=='stale_review': r['observation_id']='e:19'
        if change=='refused': r['decision']='inspect'
        if change=='gap': p['evidence']['predicted_remaining_vertical_gap_m']=float('nan')
        if change=='lateral': p['phases'][0]['hand_pose_world'][0]+=.01
        if change=='grip': p['phases'][0]['finger_position_m']=.04
        if change=='cadence': dt=1/48
        with pytest.raises(ValueError):
            reviewed_standoff_stages(p,r,'e:20',hand,.3,dt)
