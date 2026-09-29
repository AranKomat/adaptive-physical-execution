import json
import httpx
import pytest
from physical_exec.providers.responses import ProviderConfig,ResponsesProvider,extract_act
from physical_exec.errors import ProviderError,BudgetExceeded

@pytest.mark.parametrize('url',['http://example.com/v1/responses','https://a:b@example.com/v1/responses',
                               'https://example.com/v1/chat/completions','https://example.com/v1/responses?key=abc'])
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
