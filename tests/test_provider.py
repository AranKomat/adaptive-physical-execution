import json
import httpx
import pytest
from physical_exec.providers.responses import ProviderConfig,ResponsesProvider,extract_act
from physical_exec.errors import ProviderError,BudgetExceeded

@pytest.mark.parametrize('url',['http://example.com/v1/responses','https://a:b@example.com/v1/responses',
                               'https://example.com/v1/wrong','https://example.com/v1/responses?key=abc'])
def test_bad_endpoint(url):
    with pytest.raises(ValueError): ProviderConfig('configured-model',url)

def test_explicit_authorization_and_no_model_fallback(monkeypatch):
    monkeypatch.setenv('TEST_MODEL_KEY','SECRET_NOT_IN_RESULT')
    cfg=ProviderConfig('configured-model','https://example.com/v1/responses',api_key_env='TEST_MODEL_KEY',max_calls=1)
    with pytest.raises(ProviderError): ResponsesProvider(cfg)
    seen=[]
    def handle(request):
        seen.append(json.loads(request.content))
        assert request.headers['Authorization']=='Bearer SECRET_NOT_IN_RESULT'
        return httpx.Response(200,json={'status':'completed','id':'r','usage':{'input_tokens':100,'output_tokens':10},
                                      'output':[{'type':'function_call','name':'Act','arguments':'{"test":1}'}]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as c:
        p=ResponsesProvider(cfg,allow_paid=True,client=c)
        reply=p.act('instruction',[],{'type':'object','properties':{}},3)
        assert reply.arguments=={'test':1} and reply.usage.total_tokens==110
        assert seen[0]['reasoning']['effort']=='medium' and seen[0]['store'] is False
        assert seen[0]['model']=='configured-model'
        with pytest.raises(BudgetExceeded):p.act('x',[],{})
        p.close();assert p._key==''

@pytest.mark.parametrize('response',[
 {'status':'incomplete','output':[]},
 {'status':'completed','output':[{'type':'message','content':[{'type':'refusal','refusal':'no'}]}]},
 {'status':'completed','output':[{'type':'function_call','name':'exec','arguments':'{}'}]},
 {'status':'completed','output':[{'type':'function_call','name':'Act','arguments':'{"a":NaN}'}]},
 {'status':'completed','output':[{'type':'function_call','name':'Act','arguments':'{}'}]*2},
])
def test_rejects_partial_refused_bad_or_multiple_calls(response):
    with pytest.raises(ProviderError):extract_act(response)

def test_timeout_never_auto_retried(monkeypatch):
    monkeypatch.setenv('TEST_MODEL_KEY','secret');count=[]
    def handle(request):count.append(1);raise httpx.ReadTimeout('test')
    with httpx.Client(transport=httpx.MockTransport(handle)) as c:
        p=ResponsesProvider(ProviderConfig('m','https://example.com/v1/responses',api_key_env='TEST_MODEL_KEY'),allow_paid=True,client=c)
        with pytest.raises(ProviderError):p.act('x',[],{})
        assert len(count)==1 and p.calls==1 and not p.usage_log[0].usage_reported

def test_explicit_flex_provider_route(monkeypatch):
    monkeypatch.setenv('TEST_MODEL_KEY', 'secret')
    def handle(request):
        body = json.loads(request.content)
        assert body['service_tier'] == 'flex'
        assert body['provider'] == {'only': ['openai/flex'], 'allow_fallbacks': False,
                                    'require_parameters': True}
        return httpx.Response(503)
    cfg = ProviderConfig('openai/gpt-6-astra', 'https://openrouter.ai/api/v1/responses',
                         api_key_env='TEST_MODEL_KEY', service_tier='flex', provider_only='openai/flex')
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        p = ResponsesProvider(cfg, allow_paid=True, client=client)
        with pytest.raises(ProviderError, match='503'):
            p.act('x', [], {})
        assert p.calls == 1

def test_provider_routing_rejects_other_hosts():
    with pytest.raises(ValueError, match='OpenRouter'):
        ProviderConfig('m', 'https://example.com/v1/responses', provider_only='openai/flex')

def test_chat_explicit_route_preserves_tools_images_and_usage(monkeypatch):
    monkeypatch.setenv('TEST_MODEL_KEY', 'secret')
    def handle(request):
        body = json.loads(request.content)
        assert body['tools'][0]['function']['strict'] is True
        assert body['tool_choice']['function']['name'] == 'Act'
        assert body['messages'][1]['content'][1]['image_url']['url'] == 'data:image/png;base64,abc'
        return httpx.Response(200, json={'id': 'chat1', 'usage': {'prompt_tokens': 12, 'completion_tokens': 3},
            'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
                {'type': 'function', 'function': {'name': 'Act', 'arguments': '{"ok":true}'}}]}}]})
    cfg = ProviderConfig('m', 'https://openrouter.ai/api/v1/chat/completions', api_key_env='TEST_MODEL_KEY')
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        p = ResponsesProvider(cfg, allow_paid=True, client=client)
        r = p.act('task', [{'role': 'user', 'content': [{'type': 'input_text', 'text': 'state'},
            {'type': 'input_image', 'image_url': 'data:image/png;base64,abc'}]}], {'type': 'object'})
        assert r.arguments == {'ok': True} and r.usage.total_tokens == 15

@pytest.mark.parametrize('finish', ['length', 'stop', 'content_filter'])
def test_chat_rejects_non_tool_completion(finish):
    from physical_exec.providers.responses import chat_response
    with pytest.raises(ProviderError):
        extract_act(chat_response({'choices': [{'finish_reason': finish, 'message': {}}]}))

def test_chat_history_preserves_call_receipt_pair():
    from physical_exec.providers.responses import chat_request
    body = {'instructions': 'task', 'model': 'm', 'reasoning': {'effort': 'medium'},
            'max_output_tokens': 512, 'tools': [{'type': 'function', 'name': 'Act', 'strict': True}],
            'input': [{'type': 'function_call', 'call_id': 'exec_1', 'name': 'Act', 'arguments': '{"x":1}'},
                      {'type': 'function_call_output', 'call_id': 'exec_1', 'output': '{"executed":3}'}]}
    messages = chat_request(body)['messages']
    assert messages[1]['tool_calls'][0]['id'] == messages[2]['tool_call_id'] == 'exec_1'
    assert messages[1]['tool_calls'][0]['function']['arguments'] == '{"x":1}'
    assert messages[2]['content'] == '{"executed":3}'
