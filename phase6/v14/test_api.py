import unittest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from smartparse_studio.api.main import app
from smartparse_studio.api.models import AnalysisRequest


class AdaptiveApiTests(unittest.TestCase):
    def test_explicit_version_and_provider_contract(self):
        self.assertEqual(AnalysisRequest(source='').intent_version,'v12')
        self.assertEqual(AnalysisRequest(source='',intent_version='v14').intent_provider,'combined')
        with self.assertRaises(ValidationError):AnalysisRequest(source='',intent_provider='unknown')

    def test_real_header_recovery_and_source_preservation(self):
        source='#include <stdio.h>\nint main(){return 0}\n'
        with TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',51000),headers={'X-SmartParse-Studio':'1'}) as client:
            response=client.post('/api/analyze',json=dict(source=source,analyzers=['compiler'],intent_recovery=True,intent_version='v14'))
            self.assertEqual(response.status_code,200,response.text)
            body=response.json();r=body['report']['intent_recovery']
            self.assertEqual(r['algorithm'],'milestone-14');self.assertEqual(r['decision_mode'],'SYNTAX_ONLY')
            c=next(c for c in r['candidates'] if c['id']==r['recommendation'])
            self.assertEqual(c['validation']['status'],'VALID');self.assertIn('clang_fixit',c['origins'])
            self.assertIn('lower-assurance',r['reason']);self.assertTrue(body['studio']['workspace_removed'])
            self.assertTrue(body['report']['source']['original_unchanged'])
