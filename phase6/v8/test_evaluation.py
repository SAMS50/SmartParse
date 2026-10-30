import unittest
from pathlib import Path
from .evaluation import match,replay,unavailable_metrics,syntax_case
from .prepare import digest,verify_freeze


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.source=b'int read(void) { return *(int*)0; }\n'
        self.case=dict(sha256=digest(self.source),absolute_path=str(Path('example.c').resolve()),
            roots=[dict(id='root',category='memory_safety',line=1,source_evidence='*(int*)0',
                        allowed_ids=['core.NullDereference'],message_any=['null'])])
        self.d=dict(file=self.case['absolute_path'],line=1,column=24,severity='warning',
                    diagnostic_id='core.NullDereference',message='null dereference',category='unknown')

    def test_hash_mismatch(self):
        with self.assertRaises(ValueError):match(self.case,b'changed',[])

    def test_source_binding(self):
        result=match(self.case,self.source,[dict(self.d,file='foreign.c')])
        self.assertEqual(result['original_supported_proposals'],[])

    def test_meaning_not_line_only(self):
        result=match(self.case,self.source,[dict(self.d,diagnostic_id='other')])
        self.assertEqual(result['original_supported_proposals'],[])

    def test_duplicate_roots_not_warnings(self):
        r=match(self.case,self.source,[self.d,self.d,self.d])
        self.assertEqual(r['original_supported_proposals'],['root'])
        self.assertEqual(r['duplicate_support_records'],2)

    def test_notes_are_not_roots(self):
        self.assertEqual(match(self.case,self.source,[dict(self.d,severity='note')])['matches'],[])

    def test_blocked_semantics(self):
        self.assertEqual(match(self.case,self.source,[dict(self.d,_blocked=True)])['matches'],[])

    def test_conditioned_not_promoted(self):
        r=match(self.case,self.source,[dict(self.d,_conditioned=True)])
        self.assertEqual(r['original_supported_proposals'],[])
        self.assertEqual(r['conditioned_supported_proposals'],['root'])

    def test_ambiguous_evidence(self):
        self.case['roots'].append(dict(self.case['roots'][0],id='other'))
        r=match(self.case,self.source,[self.d])
        self.assertEqual(r['matches'],[])
        self.assertEqual(len(r['ambiguous']),1)

    def test_missing_metrics_not_zero(self):
        self.assertIsNone(unavailable_metrics()['precision'])
        self.assertIsNone(match(self.case,self.source,[self.d])['confirmed_defect_roots'])

    def test_delete_replay_keeps_expected_token(self):
        from smartparse import tokenize
        tokens=tokenize('int a=1,;')
        bad=next(t for t in tokens if t.value==',')
        repaired=replay(tokens,[dict(operation='delete',token=';',line=bad.line,column=bad.col)])
        self.assertEqual([t.value for t in repaired],['int','a','=','1',';',''])

    def test_unknown_repair_abstains(self):
        from smartparse import tokenize
        with self.assertRaises(ValueError):replay(tokenize('int a;'),[dict(operation='magic',token=';',line=1,column=1)])

    def test_unmapped_anchor_abstains(self):
        from smartparse import tokenize
        with self.assertRaises(ValueError):replay(tokenize('int a;'),[dict(operation='insert',token=';',line=99,column=1)])

    def test_frozen_inputs(self):self.assertGreater(verify_freeze(),30)

    def test_valid_syntax_unchanged(self):
        case=dict(roots=[])
        r=syntax_case(case,'int a=5;','validation_on','int a=5;')
        self.assertTrue(r['intended_token_stream_equal'])
        self.assertTrue(r['reached_eof'])

    def test_lexer_unsupported_explicit(self):
        r=syntax_case(dict(roots=[]),'int x=@;','panic',None)
        self.assertEqual(r['status'],'unsupported_lexer')

    def test_windows_slash_binding(self):
        from .evaluation import source_bound
        self.assertTrue(source_bound(dict(file='C:\\space dir\\a.c'),'c:/space dir/a.c'))

    def test_unknown_configuration_rejected_before_tool(self):
        from .runner import run_one
        with self.assertRaises(ValueError):run_one('nonexistent.c','invented')

    def test_missing_compiler_remains_unavailable(self):
        from unittest.mock import patch
        from .runner import run_one
        with patch('phase6.v3.engine.discover',side_effect=RuntimeError('selected compiler missing')):
            with self.assertRaisesRegex(RuntimeError,'selected compiler missing'):
                run_one('nonexistent.c','compiler_gcc6')

    def test_panic_unquoted_expected_token_is_equivalent(self):
        r=syntax_case(dict(roots=[dict(id='r',line=2,column=1,token=';',operation='insert')]),
                      'int a=1\nint b=2;','panic','int a=1;\nint b=2;')
        self.assertEqual(r['author_location_matches'],['r'])
        self.assertEqual(r['author_exact_repairs'],[])


if __name__=='__main__':unittest.main()
