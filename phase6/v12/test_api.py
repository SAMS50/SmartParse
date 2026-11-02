import unittest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from smartparse_studio.api.main import app
from smartparse_studio.api.models import AnalysisRequest
from phase6.v11.history import reconstruct


class ApiTests(unittest.TestCase):
    def test_version_contract(self):
        self.assertEqual(AnalysisRequest(source='').intent_version,'v12')
        with self.assertRaises(ValidationError):AnalysisRequest(source='',intent_version='v99')

    def test_real_worker_reliability_and_abstention(self):
        good='int f(int x){if(x){x++;}return x;}'
        bad=good.replace('}return','return');stale=bad+'}'
        with TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',51000),headers={'X-SmartParse-Studio':'1'}) as client:
            response=client.post('/api/analyze',json=dict(source=bad,analyzers=['smartparse'],intent_recovery=True,edit_history=reconstruct(stale,bad)))
            self.assertEqual(response.status_code,200,response.text)
            result=response.json();evidence=result['report']['intent_recovery']
            self.assertEqual(evidence['algorithm'],'milestone-12');self.assertIsNone(evidence['recommendation'])
            self.assertTrue(evidence['reliability']['mapping_verified']);self.assertTrue(result['report']['source']['original_unchanged'])
            self.assertTrue(result['studio']['workspace_removed'])
