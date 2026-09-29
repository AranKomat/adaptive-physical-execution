import json
import pytest
from physical_exec.stage_review import parse_review, review_messages


def test_review_has_no_execution_or_hidden_tools():
    msg = review_messages({'state': {'observation_id':'e:1'}, 'images': {'left':'abc'}}, {'error':'lift cap'})
    assert len(msg) == 1 and msg[0]['role'] == 'user'
    assert msg[0]['content'][-1]['image_url']['url'].endswith('abc')


@pytest.mark.parametrize('stage', ['reopen_hold','inspect','stop'])
def test_parse_stage(stage):
    value = dict(stage=stage,evidence='visible',uncertainty='contact',next_visual_check='support')
    assert parse_review(json.dumps(value)) == value


def test_unsupported_motion_rejected():
    with pytest.raises(ValueError):
        parse_review(json.dumps(dict(stage='lift',evidence='x',uncertainty='x',next_visual_check='x')))
