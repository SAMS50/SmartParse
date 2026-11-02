import unittest
from pydantic import ValidationError
from smartparse_studio.api.models import AnalysisRequest


class ApiTests(unittest.TestCase):
    def test_strict_history_contract(self):
        request=AnalysisRequest(source='int x;',intent_recovery=True,
            edit_history=dict(base_source='int x',base_version=0,source_version=1,
                events=[dict(version=1,offset=5,deleted='',inserted=';')]))
        self.assertEqual(request.edit_history.events[0].offset,5)
        for patch in (dict(intent_mode='fake'),dict(edit_history={'events':[]}),
                      dict(edit_history=dict(base_source='',base_version=0,source_version=1,
                        events=[dict(version=1,offset=-1,deleted='',inserted=';')]))):
            with self.assertRaises(ValidationError):AnalysisRequest(source='',**patch)
