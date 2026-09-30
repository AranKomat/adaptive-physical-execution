#!/usr/bin/env python3
"""Prepare one offline strategy review from retained public recovery evidence."""
import argparse
import base64
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--screen', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    observations = list((args.capture/'observations').glob('*.json'))
    if len(observations) != 1:
        raise ValueError('Expected exactly one retained public observation')
    state = json.loads(observations[0].read_text())
    screen = json.loads(args.screen.read_text())
    if state['observation_id'] != screen['observation_id']:
        raise ValueError('Surface screen does not match current observation')
    # This review records one specific episode, not a reusable controller prompt.
    if state['observation_id'] != '9fbd76d8e57641c79983eed82adbc2bc:2813':
        raise ValueError('Historical recovery summary requires observation2813')
    prompt = '''Propose the next materially different recovery strategy for this
simulator PC-assembly episode. This is an OFFLINE strategy review, not permission
to execute. Use only attached RGB, public proprioception, and legal depth-derived
evidence; no hidden object poses, collision truth, or evaluator is provided.

History: a GPU card was carried above its intended motherboard socket, descended,
then tipped PCB-up onto the motherboard after release and open-hand withdrawal.
Recovery inspections did not expose a usable underside. A 60-degree inclined
open-hand approach stalled about9.4mm short with increasing orientation error.
It was NOT retried or closed. A reviewed25.7mm open-hand retreat succeeded to
CURRENT2813. The hand is open; the card is NOT held. No reset allowed.

Measured planar PCB is around world z=.063m; a visible terminal span is115mm
against nominal80mm jaw opening, so full-width straddling is unavailable.
GraspGen-X produced8 high-score side grasps from a PARTIAL planar cloud, not a
whole object. All hand origins are61--71mm versus unchanged120mm execution floor.
All nominal gripper proxies extend32--43mm below world z=0; legal visible table
samples are at z=.00055--.00082m. Table continuation under the case is ASSUMED,
not measured. Several proxies intersect current measured surfaces (screen below).
Hits can include intended PCB contact, current robot, or background: NOT native
collision certification. No hits does NOT certify clearance. Three IK solutions
converged but none has qualified access. Raising these poses60mm does not resolve
all measured conflicts. Do not simply lower the floor or repeat the failed pose.
Removing the planar crop indiscriminately adds unverified coplanar geometry;
that expanded cloud was rejected. More same-cloud batches are not the next step.

We need meaningful physical recovery, not endless tiny motion/camera probes.
Consider a genuinely different accessible edge/feature grasp or a bounded
nonprehensile repositioning ONLY if supported by visible contact geometry.
Otherwise name the decisive missing evidence or capability; do not invent it.
Task goal remains successful GPU insertion with recovery, not free-space motion.
No privileged sensing, new task program, or task-specific training. Existing
local continuous DiffIK can execute bounded EEF position/orientation targets
with per-action tracking guards; those guards do not certify collision safety.
Current nominal hand-to-pinch offset is local[0,0,.1034]m. Pose quaternions wxyz.

Return JSON: observation_id, decision (propose_contact_strategy / inspect / stop),
strategy, visible_contact_evidence (camera and pixel_uv for each anchor, distinguish
visible from inferred), why_different_from_failed_attempts, required_measurements,
first_bounded_action (proposal only; do not invent precise world targets),
stop_conditions, expected_useful_effect, uncertainty. Prefer one best strategy.
If all feasible strategies need unseen contact, explicitly say so rather than
claiming an executable grasp. Do not recommend another nearby camera guess.
'''
    content = [{'type': 'text', 'text': prompt+'\nCURRENT public state: '+json.dumps(state)
                +'\nObserved-surface screen: '+json.dumps(screen)}]
    for role in ('left', 'right', 'wrist'):
        spec = state['images'][role]
        data = (args.capture/spec['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != spec['sha256']:
            raise ValueError('Image hash mismatch')
        content.extend([{'type': 'text', 'text': 'CURRENT '+role},
            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,'
                                              +base64.b64encode(data).decode()}}])
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'messages.json').write_text(json.dumps([{'role': 'user', 'content': content}]))
    print(state['observation_id'])


if __name__ == '__main__':
    main()
