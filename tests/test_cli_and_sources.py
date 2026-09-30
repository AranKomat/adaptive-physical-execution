import json
from pathlib import Path
import subprocess
import sys
import pytest
from physical_exec.cli import main
from physical_exec.config import load_task

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('task',['pc_gpu','pc_ram','pc_gpu_ram','bulb'])
def test_task_configs(task):
    cfg,limits=load_task(ROOT/'configs/tasks'/f'{task}.json')
    assert cfg['preset']==f'assembly.{task}.franka.joint'
    assert len(set(cfg['camera_map'].values()))==3


def test_all_offline_commands(tmp_path):
    assert main(['doctor','--task',str(ROOT/'configs/tasks/pc_gpu.json')])==0
    assert main(['smoke','--output',str(tmp_path/'smoke')])==0
    assert main(['verify-trace',str(tmp_path/'smoke/direct_roboicl')])==0
    assert main(['report',str(tmp_path/'smoke/hybrid')])==0
    assert main(['compare',str(tmp_path/'smoke/hybrid'),str(tmp_path/'smoke/direct_roboicl'),'--output',str(tmp_path/'cmp')])==0


def test_paid_run_requires_explicit_opt_in(tmp_path):
    assert main(['run','--task',str(ROOT/'configs/tasks/pc_gpu.json'),'--mode','direct_roboicl',
                 '--model','test','--endpoint','https://example.com/v1/responses','--output',str(tmp_path/'no')])==2
    assert not (tmp_path/'no').exists()


def test_enhanced_task_bounds_and_camera_parity(tmp_path):
    enhanced,limits=load_task(ROOT/'configs/tasks/pc_gpu_enhanced.json')
    original,baseline=load_task(ROOT/'configs/tasks/pc_gpu_grasp_wrist_aim.json')
    for key in ('preset','camera_map','extra_cameras','wrist_target_hand','control_hz','image_size'):
        assert enhanced[key]==original[key]
    assert limits.max_translation_m==.2 and limits.max_rotation_rad==.3
    assert limits.max_joint_step_rad==baseline.max_joint_step_rad
    assert enhanced['requires_local_eef_execution'] is True
    assert main(['run','--task',str(ROOT/'configs/tasks/pc_gpu_enhanced.json'),
                 '--mode','direct_roboicl','--model','test','--allow-paid',
                 '--endpoint','https://example.com/v1/responses',
                 '--output',str(tmp_path/'no')])==2
    assert not (tmp_path/'no').exists()


def test_upstream_bootstrap_is_plan_only_by_default(tmp_path):
    completed=subprocess.run([sys.executable,str(ROOT/'scripts/bootstrap_upstreams.py'),'--destination',str(tmp_path/'upstream')],
                             capture_output=True,text=True,check=True)
    assert 'Plan only' in completed.stdout and not (tmp_path/'upstream').exists()


def test_native_profile_replaces_gateway_without_running_it(tmp_path):
    repo=tmp_path/'repo';(repo/'configs/protocols').mkdir(parents=True)
    (repo/'configs/protocols/zero_shot_b25.json').write_text(json.dumps({'id':'original','model':'unwanted-alias',
        'endpoint':'https://thirdparty.invalid/v1/responses','harness_overrides':{'reasoning_effort':'xhigh'}}))
    dest=tmp_path/'profile.json'
    subprocess.run([sys.executable,str(ROOT/'scripts/make_native_roboicl_profile.py'),'--repo',str(repo),
                    '--model','authorized-model','--endpoint','https://example.com/v1/responses','--output',str(dest)],check=True)
    obj=json.loads(dest.read_text());assert obj['model']=='authorized-model'
    assert obj['endpoint']=='https://example.com/v1/responses' and obj['harness_overrides']['reasoning_effort']=='medium'
