"""Bounds for explicit simulator-only local correction, not collision certification."""
import numpy as np

from .errors import InputRejected
from .geometry import finite_vector, pose_error, unit_quaternion


def validate_local_stage(value, observation, *, allow_inspection_camera=False,
                         last_gripper_command=None):
    required = {'observation_id', 'hand_pose_world', 'gripper_open', 'max_steps', 'target_source'}
    fields = set(value) if isinstance(value, dict) else set()
    camera = 'camera_eye_world' in fields
    if camera and not allow_inspection_camera:
        raise InputRejected('inspection camera not enabled')
    optional = ({'camera_eye_world'} if camera else set()) | ({'settle_at_end'} if 'settle_at_end' in fields else set())
    if camera and 'camera_gaze_world' in fields:
        optional.add('camera_gaze_world')
    if not isinstance(value, dict) or fields != required | optional:
        raise InputRejected('invalid local-stage fields')
    if 'settle_at_end' in value and type(value['settle_at_end']) is not bool:
        raise InputRejected('settle_at_end must be boolean')
    if camera and value.get('settle_at_end') is False:
        raise InputRejected('camera inspection requires endpoint settling')
    if value['observation_id'] != observation.key:
        raise InputRejected('stale local stage')
    try:
        pose = finite_vector(value['hand_pose_world'], 7).copy()
        pose[3:] = unit_quaternion(pose[3:])
    except (ValueError, TypeError) as exc:
        raise InputRejected('invalid local-stage pose') from exc
    delta = pose_error(observation.eef_pose, pose)
    if np.any(pose[:3] < [-.1, -.8, .12]) or np.any(pose[:3] > [.9, .6, .8]):
        raise InputRejected('local-stage target outside pilot workcell')
    if np.linalg.norm(delta[:3]) > .20 or np.linalg.norm(delta[3:]) > .30:
        raise InputRejected('local-stage displacement exceeds 20 cm / 0.30 rad')
    if type(value['max_steps']) is not int or not 1 <= value['max_steps'] <= 64:
        raise InputRejected('local stage requires 1..64 control actions')
    opening = value['gripper_open']
    if isinstance(opening, bool) or not isinstance(opening, (float, int)) or not np.isfinite(opening) or not 0 <= opening <= 1:
        raise InputRejected('invalid gripper opening')
    if not isinstance(value['target_source'], str) or not 1 <= len(value['target_source']) <= 2000:
        raise InputRejected('explicit target provenance required')
    if camera:
        if np.linalg.norm(delta[:3]) > .003 or np.linalg.norm(delta[3:]) > .03:
            raise InputRejected('inspection camera requires arm hold')
        if last_gripper_command is None or abs(opening-last_gripper_command) > 1e-8:
            raise InputRejected('inspection camera must preserve previous gripper command')
        try:
            finite_vector(value['camera_eye_world'], 3)
            if 'camera_gaze_world' in value:
                finite_vector(value['camera_gaze_world'], 3)
        except (ValueError, TypeError) as exc:
            raise InputRejected('invalid camera eye') from exc
    return pose
