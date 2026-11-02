import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from phase6.v11.history import reconstruct
from .acquire import fetch
from .ingest import normalize,sha,tokens,privacy_or_safety,ingest_rows
from .history import build_input,RecoveryInput
from .compiler import apply_fixits,diagnostics,Compiler
from .metrics import label_case,observation,summarize,rate,paired_bootstrap,wilson
from .engine import evaluate_input


def row(source,target):return dict(sourceText=source,targetText=target,sourceTime='2015-10-01 10:00:00',targetTime='2015-10-01 10:01:00')


class IngestionTests(unittest.TestCase):
    def test_hash_normalization_and_token_comparison(self):
        source='int x;\r\n';self.assertNotEqual(sha(source),sha(normalize(source)))
        self.assertEqual(normalize('\ufeff'+source),'int x;\n')
        self.assertEqual(tokens('int x; /* comment */'),tokens('int\n x ;'))
        self.assertNotEqual(tokens('x++'),tokens('x + +'))

    def test_dedup_source_family_split_determinism(self):
        rows=[row('int alpha(int x){return x}', 'int alpha(int x){return x;}'),
              row('int beta(int y){return y}', 'int beta(int y){return y;}'),
              row('int g(){int x=0 while(x<5){x++;}return x;}', 'int g(){int x=0;while(x<5){x++;}return x;}')]
        a,meta=ingest_rows(rows,development=1,final=2);b,other=ingest_rows(rows,development=1,final=2)
        self.assertEqual(a,b);self.assertEqual(meta,other)
        self.assertEqual(meta['counts']['normalized_duplicate_pair'],1)
        self.assertFalse({c['family'] for c in a if c['split']=='development'}&{c['family'] for c in a if c['split']=='final'})
        self.assertTrue(all(c['history'] is None for c in a))

    def test_chronology_privacy_and_include_filter(self):
        for source in ('#include "/private/secret.h"\nint x;', '#pragma GCC poison int', '#include <stdio.h>\n// name: Private Student', '%:include "x.h"', '#inc\\\nlude "x.h"'):
            self.assertIsNotNone(privacy_or_safety(source))
        self.assertIsNone(privacy_or_safety('#include <stdio.h>\nint main(){return 0;}'))
        r=row('int x','int x;');r['sourceTime']=r['targetTime']
        data,meta=ingest_rows([r]);self.assertEqual(data,[]);self.assertEqual(meta['counts']['nonchronological_endpoints'],1)

    def test_acquisition_hash_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'cached';path.write_bytes(b'legitimate cache')
            self.assertEqual(fetch('https://example.invalid',path,100,sha(b'legitimate cache'))['bytes'],16)
            with self.assertRaisesRegex(ValueError,'hash mismatch'):fetch('https://example.invalid',path,100,'different')

    def test_prepared_provenance_rejects_source_tampering(self):
        from .evaluate import load_cases
        cases,meta=ingest_rows([row('int f(){return 0}','int f(){return 0;}')],development=1,final=0)
        public={**meta,'cases':[{k:v for k,v in c.items() if k not in ('source','reference','raw_source','raw_reference','source_time','target_time','history')} for c in cases]}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'manifest.json').write_text(json.dumps(public));(root/'frozen.json').write_text(json.dumps(public))
            (root/'cases.json').write_text(json.dumps(cases));self.assertEqual(len(load_cases(root,root/'frozen.json')[0]),1)
            cases[0]['source']='int malicious;';(root/'cases.json').write_text(json.dumps(cases))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):load_cases(root,root/'frozen.json')


class LeakageTests(unittest.TestCase):
    def test_no_reference_field_or_dict_crosses_engine_boundary(self):
        with self.assertRaises(TypeError):RecoveryInput(source='int x',reference='int x;')
        with self.assertRaises(TypeError):evaluate_input({'source':'int x','reference':'int x;'})
        self.assertIsNone(build_input('int x','2015-10-01 10:00:00').history)

    def test_future_snapshot_is_rejected(self):
        h=reconstruct('int x;','int x')
        e=dict(kind='partial',provenance_url='https://example.org/real-snapshot',base_time='2015-10-01 10:01:00',event_times=['2015-10-01 10:02:00'],history=h)
        with self.assertRaisesRegex(ValueError,'Future'):build_input('int x','2015-10-01 10:00:00',e)
        e['base_time']='2015-10-01 09:58:00';e['event_times']=['2015-10-01 09:59:00']
        self.assertEqual(build_input('int x','2015-10-01 10:00:00',e).history_condition,'partial')
        del e['provenance_url']
        with self.assertRaisesRegex(ValueError,'provenance'):build_input('int x','2015-10-01 10:00:00',e)


class CompilerTests(unittest.TestCase):
    def test_diagnostic_and_machine_fixit_extraction(self):
        from phase6.v3.policy import fixits
        data=b'<stdin>:1:6: error: expected semicolon\nfix-it:"<stdin>":{1:6-1:6}:";"\n'
        ds=diagnostics(data.decode());self.assertEqual(ds[0]['category'],'syntax/delimiter')
        repaired,why=apply_fixits('int x',fixits(data));self.assertEqual(repaired,'int x;')

    def test_ambiguous_ranges_and_utf8_offsets(self):
        edit=dict(file='<stdin>',start_line=1,start_column=6,end_line=1,end_column=6,replacement=';')
        self.assertIsNone(apply_fixits('int x',[edit,edit])[0])
        self.assertIsNone(apply_fixits('int x',[{**edit,'file':'other.h'}])[0])
        bad={**edit,'start_column':2,'end_column':2}
        self.assertIsNone(apply_fixits('éx',[bad])[0])
        self.assertEqual(apply_fixits('int x',[])[1],'no machine fix-it edits')

    def test_unsupported_compiler_is_not_zero_accuracy(self):
        with patch('phase6.v13.compiler.locate',return_value=None):tool=Compiler('gcc')
        self.assertEqual(tool.check('int x;')['status'],'unavailable')
        self.assertIsNone(rate(0,0)['estimate'])

    def test_real_compiler_syntax_and_fixits(self):
        tool=Compiler('clang')
        if tool.identity['status']!='available':self.skipTest('Clang unavailable')
        result=tool.repair('int f(){return 0}')
        self.assertFalse(result['original']['accepted'])
        self.assertTrue(result['applicable']);self.assertTrue(result['validation']['accepted'])
        self.assertEqual(result['repaired_source'],'int f(){return 0;}')


class MetricTests(unittest.TestCase):
    def test_category_A_requires_same_compiler_pair(self):
        source={'gcc':dict(status='completed',accepted=False),'clang':dict(status='completed',accepted=True)}
        refs={'gcc':dict(status='completed',accepted=False),'clang':dict(status='completed',accepted=True)}
        self.assertEqual(label_case(source,refs)[0],'B')
        refs['gcc']['accepted']=True;self.assertEqual(label_case(source,refs)[0],'A')

    def test_exact_token_and_compile_are_not_equivalence(self):
        candidate=dict(id='c',source='int x ;',validation={'status':'VALID'},score=10,semantic={})
        obs=observation(dict(candidates=[candidate],recommendation='c',decision='recommended',reason='test'), 'int x;')
        self.assertFalse(obs['exact']);self.assertTrue(obs['token_match']);self.assertTrue(obs['compilation_success']);self.assertTrue(obs['wrong'])
        self.assertEqual(obs['behavioral_equivalence'],'not assessed')
        self.assertEqual(summarize([obs])['accuracy_when_recommended']['denominator'],1)

    def test_intervals_zero_event_and_paired_determinism(self):
        self.assertGreater(wilson(0,80)[1],0);self.assertIsNone(wilson(0,0))
        rows=[dict(family=str(i),systems=dict(old={'exact':False},new={'exact':True})) for i in range(4)]
        a=paired_bootstrap(rows,'old','new');b=paired_bootstrap(rows,'old','new')
        self.assertEqual(a,b);self.assertEqual(a['mean_difference'],1);self.assertEqual(a['right_only'],4)


if __name__=='__main__':unittest.main()
