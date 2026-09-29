from pathlib import Path
import sys
import pytest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.contracts import Observation

@pytest.fixture
def observation():
    return Observation('episode',0,0,'Install the module.','franka',
                       {'wrist':np.zeros((40,60,3),dtype=np.uint8),'left':np.ones((40,60,3),dtype=np.uint8),
                        'right':np.full((40,60,3),2,dtype=np.uint8)},
                       np.zeros(7),tuple(f'panda_joint{i}' for i in range(1,8)),
                       np.array([.4,0,.4,1,0,0,0]),.7,1/15)

@pytest.fixture
def urdf_file(tmp_path):
    # Manufactured TEST chain, not a Panda or a benchmark robot.
    links=['base','x','y','z','rx','ry','rz','tool']
    joints=[]
    for i,(kind,axis) in enumerate([('prismatic','1 0 0'),('prismatic','0 1 0'),('prismatic','0 0 1'),
                                     ('revolute','1 0 0'),('revolute','0 1 0'),('revolute','0 0 1')]):
        joints.append(f'<joint name="j{i}" type="{kind}"><parent link="{links[i]}"/><child link="{links[i+1]}"/><axis xyz="{axis}"/><limit lower="-2" upper="2"/></joint>')
    joints.append('<joint name="tool_joint" type="fixed"><parent link="rz"/><child link="tool"/><origin xyz="0 0 0.1"/></joint>')
    p=tmp_path/'test.urdf';p.write_text('<robot name="test">'+''.join(f'<link name="{x}"/>' for x in links)+''.join(joints)+'</robot>')
    return p
