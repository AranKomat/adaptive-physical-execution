from dataclasses import replace
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest
from physical_exec.memory import ExecutionMemory,MemoryConfig,enforce_context_budget,reference_from_run
from physical_exec.third_party.trajectory_memory import LiveTrajectoryMemory
from physical_exec.contracts import ActionChunk,ExecutionReceipt
from physical_exec.trace import dumps


def test_vendored_memory_exact_upstream_blob():
    p=Path(__file__).resolve().parents[1]/'src/physical_exec/third_party/trajectory_memory.py'
    b=p.read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()=='8542840fa65ff9fc8fcc5d3e15361473a51ae499'


def test_anchor_bounds_latest_and_gaps():
    m=LiveTrajectoryMemory(3,10,True);m.configure(60)
    for s in range(0,60,5): m.capture(s,s+5,[{'role':'user','content':[{'type':'input_text','text':str(s)}]}],{'executed':5})
    assert m.stats['retained_chunks']<=3
    assert m.stats['latest_interval']==[55,60]
    out=m.render({'role':'user','content':[{'type':'input_text','text':'INIT'}]},60,
                 lambda s:{'role':'user','content':[{'type':'input_text','text':f'OBS{s}'}]})
    text=dumps(out);assert 'TRAJECTORY_GAP' in text and 'OBS60' in text and 'Do not infer continuity' in text
    assert 'anchor_steps' not in text


def test_anchor_idempotence_conflict_and_rejected_zero():
    m=LiveTrajectoryMemory(3,10,True)
    assert not m.capture(0,0,[])
    m.capture(0,3,[{'test':1}]);m.capture(0,3,[{'test':1}])
    assert m.stats['captured_chunks']==1
    with pytest.raises(ValueError): m.capture(0,3,[{'test':2}])
    with pytest.raises(ValueError): m.capture(2,4,[])


def test_memory_actual_receipts_not_privileged_labels(observation):
    m=ExecutionMemory(MemoryConfig(anchor_count=3),maximum_steps=30);m.observe(observation)
    after=replace(observation,seq=2,sim_time=2/15)
    a=ActionChunk('eef_delta_world',[[0,0,0,0,0,0,.7]]*3,observation.key,observation.control_dt,'test')
    receipt=ExecutionReceipt('cmd',observation.key,after.key,3,2,'interrupted','host ended chunk','test',2/15,.1)
    m.commit(observation,after,a,receipt,{'intent':'Pick the part','actions':'MODEL_AUTHORED'})
    text=dumps(m.render(after))
    assert 'executed_steps' in text and 'MODEL_AUTHORED' in text
    assert 'object_pose' not in text and 'score_host_only' not in text
    assert 'executed_command' in text
    assert m.anchors.stats['latest_interval']==[0,2]
    m.set_summary('The part may have moved.',[0,2])
    assert 'model_authored_unverified_summary' in dumps(m.render(after))
    with pytest.raises(ValueError): m.set_summary('something',[3])


def test_memory_episode_isolation_and_budget(observation):
    m=ExecutionMemory(MemoryConfig(max_images=1));m.render(observation)
    with pytest.raises(ValueError): m.observe(replace(observation,episode_id='other'))
    with pytest.raises(ValueError): enforce_context_budget([{'role':'user','content':[{'type':'input_image'},{'type':'input_image'}]}],m.config)
    m.reset();m.observe(replace(observation,episode_id='other'))


def test_rejection_tail_is_not_an_anchor(observation):
    m=ExecutionMemory(MemoryConfig());m.observe(observation)
    for i in range(8):m.reject('bad input '+str(i))
    assert len(m.rejections)==3 and m.anchors.stats['captured_chunks']==0
    assert 'nothing executed' in dumps(m.render(observation))
