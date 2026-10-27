"""Independent coverage/accounting tests, not new defect-detection rules."""
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import uuid
import sys
import unittest
from unittest.mock import patch

from extended_c import AnalysisResult, Compiler, Diagnostic
from phase6.v2.eligibility import (build_report, coverage, parse_checkers, parse_includes, parse_macros,
                                  pass_blockers, probe)
from phase6.v2.regions import functions_from_ast, same_path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'fixtures/semantic_failure.c'
CLANG=Compiler('clang','clang','test version',('-Wall',))


def ast_function(data, name, *, file=None, invalid=False):
    spelling=name.encode()
    name_start=data.index(spelling+b'(')
    start=data.rfind(b'\n',0,name_start)+1
    body=data.index(b'{',name_start)
    end=data.index(b'}',body)
    return {'kind':'FunctionDecl','name':name,'loc':{'file':file or str(SOURCE),'offset':name_start},
            'isInvalid':invalid,'range':{'begin':{'offset':start},'end':{'offset':end}},
            'inner':[{'kind':'CompoundStmt','range':{'begin':{'offset':body},'end':{'offset':end}}}]}


def fake_probes(command, timeout, data=None):
    record={'command':list(command),'status':'completed','returncode':0,'stderr':'','stdout_sha256':'test','stdout_bytes':0}
    if '-dumpmachine' in command: raw=b'x86_64-test-windows\n'
    elif '-dM' in command: raw=b'#define __STDC__ 1\n#define __STDC_VERSION__ 201112L\n'
    elif '-v' in command:
        raw=b''; record['stderr']='#include <...> search starts here:\n C:/a folder/include\nEnd of search list.\n'
    elif '-analyzer-list-enabled-checkers' in command: raw=b'OVERVIEW: Clang Static Analyzer Enabled Checkers List\ncore.NullDereference\nunix.Malloc\n'
    elif '-ast-dump=json' in command:
        tree={'kind':'TranslationUnitDecl','inner':[]}
        if command[-1]!='-':
            source=SOURCE.read_bytes()
            tree['inner']=[ast_function(source,n) for n in ('identity','broken_call','otherwise_valid')]
        raw=json.dumps(tree).encode()
    else: raw=b'preprocessed source'
    return record,raw


def result(errors=False, analyzer=False):
    report=AnalysisResult('completed',CLANG,returncode=1 if errors else 0,command=('clang','-fsyntax-only',str(SOURCE)))
    if errors:
        report.diagnostics=[Diagnostic(str(SOURCE),2,1,'error','too many arguments to function call','clang','semantic/type')]
    if analyzer:
        report.static_analysis=AnalysisResult('partial' if errors else 'completed',CLANG,
            diagnostics=list(report.diagnostics),returncode=1 if errors else 0,command=('clang','--analyze',str(SOURCE)),findings=[])
    return report


class RegionTests(unittest.TestCase):
    def test_physical_main_file_functions(self):
        data=SOURCE.read_bytes()
        tree={'kind':'TranslationUnitDecl','inner':[ast_function(data,'identity'),ast_function(data,'otherwise_valid')]}
        regions,excluded=functions_from_ast(tree,str(SOURCE),data)
        self.assertEqual([r['name'] for r in regions],['identity','otherwise_valid'])
        self.assertFalse(excluded)
        self.assertEqual(regions[1]['start_line'],3)

    def test_headers_are_not_main_file_regions(self):
        data=SOURCE.read_bytes()
        tree={'kind':'TranslationUnitDecl','inner':[ast_function(data,'identity',file='C:/header.h')]}
        self.assertEqual(functions_from_ast(tree,str(SOURCE),data)[0],[])

    def test_macro_generated_definition_is_excluded(self):
        data=SOURCE.read_bytes(); node=ast_function(data,'identity')
        node['loc']={'file':str(SOURCE),'expansionLoc':{'offset':0},'spellingLoc':{'offset':1}}
        regions,excluded=functions_from_ast({'kind':'TranslationUnitDecl','inner':[node]},str(SOURCE),data)
        self.assertFalse(regions); self.assertTrue(excluded)

    def test_invalid_recovery_ast_is_not_trusted(self):
        data=SOURCE.read_bytes(); node=ast_function(data,'identity',invalid=True)
        regions,excluded=functions_from_ast({'kind':'TranslationUnitDecl','inner':[node]},str(SOURCE),data)
        self.assertFalse(regions); self.assertTrue(excluded)

    def test_offsets_must_match_source(self):
        data=SOURCE.read_bytes(); node=ast_function(data,'identity'); node['loc']['offset']=999999
        regions,excluded=functions_from_ast({'kind':'TranslationUnitDecl','inner':[node]},str(SOURCE),data)
        self.assertFalse(regions); self.assertTrue(excluded)

    def test_windows_paths_case_and_spaces(self):
        self.assertTrue(same_path('C:\\A Folder\\FILE.c','c:/a folder/file.c'))
        self.assertFalse(same_path('C:/a/file.c','C:/b/file.c'))

    def test_malformed_ast_rejected(self):
        for tree in ([],{'kind':'garbage','inner':[]},{'kind':'TranslationUnitDecl','inner':[{'loc':None}]},
                     {'kind':'TranslationUnitDecl','inner':[{'kind':'FunctionDecl','loc':{'spellingLoc':{},'expansionLoc':None}}]},
                     {'kind':'TranslationUnitDecl','inner':[{'kind':'FunctionDecl','loc':{},'inner':None}]}):
            with self.assertRaises(ValueError): functions_from_ast(tree,str(SOURCE),b'')

    def test_presumed_line_does_not_override_physical_offset(self):
        data=SOURCE.read_bytes(); node=ast_function(data,'otherwise_valid')
        node['loc'].update(presumedLine=700,presumedFile='generated.c')
        regions,_=functions_from_ast({'kind':'TranslationUnitDecl','inner':[node]},str(SOURCE),data)
        self.assertEqual(regions[0]['start_line'],3)

    def test_filename_elision_after_macro_does_not_lose_ordinary_body(self):
        data=SOURCE.read_bytes()
        macro=ast_function(data,'identity')
        macro['loc']={'spellingLoc':{'file':str(SOURCE),'offset':4},'expansionLoc':{'offset':0}}
        ordinary=ast_function(data,'otherwise_valid'); del ordinary['loc']['file']
        regions,excluded=functions_from_ast({'kind':'TranslationUnitDecl','inner':[macro,ordinary]},str(SOURCE),data)
        self.assertEqual([r['name'] for r in regions],['otherwise_valid'])
        self.assertEqual(len(excluded),1)


class ManifestTests(unittest.TestCase):
    def build(self,report):
        with patch('phase6.v2.eligibility.probe',side_effect=fake_probes), \
             patch('phase6.v2.eligibility.tempfile.TemporaryDirectory',return_value=nullcontext(str(HERE/'outputs'))):
            return build_report(SOURCE,report,standard='c11',include_dirs=['include folder'],defines=['FEATURE=1'])

    def test_valid_compiler_function_coverage(self):
        report=self.build(result())
        self.assertEqual(report['manifest']['source']['sha256'],hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual(report['manifest']['requested_standard'],'c11')
        self.assertEqual(report['manifest']['macro_definitions'],['FEATURE=1'])
        self.assertEqual(report['manifest']['tool_contexts']['compiler']['target'],'x86_64-test-windows')
        self.assertTrue(all(r['compiler_coverage']['status']=='completed' for r in report['regions']))
        self.assertTrue(all(r['analyzer_coverage']['status']=='not_attempted' for r in report['regions']))
        self.assertEqual(json.loads(json.dumps(report))['schema_version'],'1.0')

    def test_no_function_analysis_inference_from_nearby_diagnostic(self):
        report=self.build(result(errors=True,analyzer=True))
        unaffected=next(r for r in report['regions'] if r['name']=='otherwise_valid')
        self.assertEqual(unaffected['compiler_coverage']['status'],'blocked')
        self.assertEqual(unaffected['analyzer_coverage']['status'],'blocked')
        self.assertEqual(report['stages']['compiler']['completion'],'completed')
        self.assertEqual(report['stages']['analyzer']['completion'],'partial')
        self.assertIn('semantic/type',{b['category'] for b in report['blockers']})

    def test_completed_analyzer_does_not_certify_per_function_exploration(self):
        report=self.build(result(analyzer=True))
        self.assertTrue(all(r['analyzer_coverage']['status']=='unknown' for r in report['regions']))
        checkers=report['manifest']['tool_contexts']['analyzer']['enabled_default_checkers']
        self.assertEqual(checkers,['core.NullDereference','unix.Malloc'])

    def test_gcc_falls_back_to_translation_unit(self):
        value=result(); value.compiler=Compiler('gcc','gcc','6.3',('-Wall',))
        report=self.build(value)
        self.assertEqual(len(report['regions']),1)
        self.assertEqual(report['region_inventory']['status'],'unsupported')

    def test_malformed_tool_output_keeps_unknown_coverage(self):
        def malformed(command,timeout,data=None):
            record,raw=fake_probes(command,timeout,data)
            if '-ast-dump=json' in command: raw=b'not json'
            return record,raw
        with patch('phase6.v2.eligibility.probe',side_effect=malformed): report=build_report(SOURCE,result())
        self.assertEqual(report['region_inventory']['status'],'unknown')
        self.assertEqual(len(report['regions']),1)

    def test_unavailable_metadata_does_not_guess_target(self):
        def unavailable(command,timeout,data=None):
            return {'command':command,'status':'failed','returncode':1,'stderr':'unsupported'},b''
        with patch('phase6.v2.eligibility.probe',side_effect=unavailable): report=build_report(SOURCE,result())
        self.assertIsNone(report['manifest']['tool_contexts']['compiler']['target'])
        self.assertEqual(report['manifest']['tool_contexts']['compiler']['standard_selection'],'compiler_default')

    def test_source_encoding_is_not_rewritten(self):
        with patch('phase6.v2.eligibility.Path.read_bytes',return_value=b'\xff\n'),patch('phase6.v2.eligibility.probe',side_effect=fake_probes):
            report=build_report(SOURCE,AnalysisResult('failed'))
        self.assertEqual(report['manifest']['source']['encoding'],'unknown/non-UTF-8')


class CompletionAndBlockerTests(unittest.TestCase):
    def test_syntax_classification(self):
        value=result(); value.diagnostics=[Diagnostic('x.c',1,1,'error',"expected ';'",'gcc','syntax')]
        self.assertEqual(pass_blockers(value,'compiler')[0]['category'],'syntax')

    def test_preprocessing_classification(self):
        value=result(); value.diagnostics=[Diagnostic('x.c',1,1,'fatal error','missing.h: No such file or directory','gcc')]
        self.assertEqual(pass_blockers(value,'compiler')[0]['category'],'preprocessing/configuration')

    def test_preprocessing_failure_does_not_relabel_known_type_error(self):
        self.assertEqual(pass_blockers(result(errors=True),'compiler',True)[0]['category'],'semantic/type')

    def test_timeout_distinct_from_completed(self):
        value=AnalysisResult('timed_out',command=('clang',),issues=['Compiler timed out after 1 second'])
        self.assertEqual(pass_blockers(value,'compiler')[0]['category'],'timeout')
        self.assertEqual(coverage(value,'compiler')['status'],'unknown')

    def test_analyzer_unavailable_is_not_attempted(self):
        value=AnalysisResult('unavailable',issues=['unsupported analyzer'])
        self.assertEqual(coverage(value,'analyzer')['status'],'not_attempted')
        self.assertEqual(pass_blockers(value,'analyzer')[0]['category'],'analyzer limitations')

    def test_unknown_output_not_assumed_syntax(self):
        value=result(); value.unrecognized_output=['???']; value.status='partial'
        self.assertEqual(pass_blockers(value,'compiler')[0]['category'],'analyzer limitations')
        self.assertEqual(coverage(value,'compiler')['status'],'unknown')

    def test_probe_timeout_retains_partial_output(self):
        with patch('phase6.v2.eligibility._run',side_effect=subprocess.TimeoutExpired('clang',1,output=b'partial',stderr=b'bad')):
            record,raw=probe(['clang'],1)
        self.assertEqual(record['status'],'timed_out'); self.assertEqual(raw,b'partial')

    def test_probe_os_error_is_recorded(self):
        with patch('phase6.v2.eligibility._run',side_effect=OSError('cannot start')):
            record,_=probe(['clang'],1)
        self.assertIn('cannot start',record['issue'])

    def test_metadata_parsers_reject_unrecognized_output(self):
        self.assertIsNone(parse_checkers('gibberish'))
        self.assertIsNone(parse_checkers('OVERVIEW: Clang Static Analyzer Enabled Checkers List\n'))
        self.assertIsNone(parse_includes('C:/something'))
        self.assertEqual(parse_macros('not a macro'),{})

    def test_invalid_metadata_timeout_rejected_before_probe(self):
        with patch('phase6.v2.eligibility.probe') as run:
            with self.assertRaises(ValueError): build_report(SOURCE,result(),metadata_timeout=0)
        run.assert_not_called()


class OptInCliTests(unittest.TestCase):
    def test_existing_cli_has_no_eligibility_side_effect(self):
        from analyze_c import build_parser
        self.assertNotIn('metadata_timeout',vars(build_parser().parse_args(['input.c'])))

    def test_new_json_envelope_keeps_original_analysis_nested(self):
        import io
        from contextlib import redirect_stdout
        from phase6.v2.__main__ import main
        report={'schema':'smartparse.analysis_eligibility','schema_version':'1.0',
                'manifest':{'source':{'original_source_unchanged':True}},'analysis':{'schema_version':'1.0'}}
        with patch('phase6.v2.__main__.analyze_eligibility',return_value=(report,result())),redirect_stdout(io.StringIO()) as out:
            code=main(['C:\\folder with spaces\\input.c','--compiler','C:\\LLVM Folder\\clang.exe','--json'])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(out.getvalue())['analysis']['schema_version'],'1.0')


class LiveEligibilityTests(unittest.TestCase):
    def clang(self):
        value=shutil.which('clang')
        if not value: self.skipTest('Clang not on process PATH; live region inventory pending')
        return value

    def analyze(self,name,**kwargs):
        from phase6.v2.eligibility import analyze_eligibility
        compiler=self.clang()
        source=HERE/'fixtures'/name
        before=source.read_bytes()
        report,_=analyze_eligibility(source,preference='clang',executable=compiler,metadata_timeout=10,**kwargs)
        self.assertEqual(source.read_bytes(),before)
        return report

    def test_live_valid_header_context_and_function_inventory(self):
        report=self.analyze('valid_context.c',standard='c11',defines=['INITIAL_VALUE=9'])
        self.assertEqual(report['stages']['compiler']['returncode'],0,report['analysis'])
        self.assertEqual([r['name'] for r in report['regions'][1:]],['item_value','main'])
        self.assertNotIn('header_value',[r['name'] for r in report['regions']])
        self.assertEqual(report['manifest']['tool_contexts']['compiler']['standard_macros']['__STDC_VERSION__'],'201112L')
        self.assertEqual(report['manifest']['macro_definitions'],['INITIAL_VALUE=9'])

    def test_live_preprocessing_failure_blocks_translation_unit(self):
        report=self.analyze('preprocessing_failure.c')
        self.assertEqual(report['stages']['preprocessing_probe']['status'],'failed')
        self.assertIn('preprocessing/configuration',{b['category'] for b in report['blockers']})
        self.assertEqual(report['regions'][0]['compiler_coverage']['status'],'blocked')

    def test_live_syntax_failure_does_not_certify_unaffected_function(self):
        report=self.analyze('syntax_failure.c')
        self.assertIn('syntax',{b['category'] for b in report['blockers']})
        self.assertEqual(report['stages']['preprocessing_probe']['status'],'completed')
        self.assertTrue(all(r['compiler_coverage']['status']=='blocked' for r in report['regions']))

    def test_live_semantic_failure_and_partial_analyzer(self):
        compiler=self.clang()
        report=self.analyze('semantic_failure.c',static_analysis=True,analyzer_executable=compiler)
        if report['stages']['analyzer']['completion']=='unavailable': self.skipTest('Analyzer not usable in this environment')
        self.assertEqual(report['stages']['compiler']['completion'],'completed')
        self.assertEqual(report['stages']['analyzer']['completion'],'partial')
        self.assertTrue(all(r['analyzer_coverage']['status']=='blocked' for r in report['regions']))

    def test_live_configuration_switch_uses_same_unchanged_source(self):
        blocked=self.analyze('config_required.c')
        accepted=self.analyze('config_required.c',defines=['ENABLE_FEATURE=1'])
        self.assertEqual(blocked['stages']['preprocessing_probe']['status'],'failed')
        self.assertTrue(accepted['stages']['compiler']['frontend_accepted'])
        self.assertEqual(blocked['manifest']['source']['sha256'],accepted['manifest']['source']['sha256'])

    def test_live_macro_definition_not_given_guessed_region(self):
        report=self.analyze('macro_regions.c')
        self.assertTrue(report['stages']['compiler']['frontend_accepted'])
        names=[r['name'] for r in report['regions'][1:]]
        self.assertIn('ordinary_function',names)
        self.assertNotIn('generated_function',names)
        self.assertTrue(report['region_inventory']['exclusions'])

    def test_live_cli_with_space_path_and_include_directory(self):
        compiler=self.clang()
        source=HERE/'outputs'/('new source '+uuid.uuid4().hex+'.c')
        source.write_bytes((HERE/'fixtures/valid_context.c').read_bytes())
        before=source.read_bytes()
        try:
            process=subprocess.run([sys.executable,'-m','phase6.v2',str(source),'--compiler',compiler,
                        '-I',str(HERE/'fixtures'),'--std','c11','--json'],capture_output=True,timeout=30,shell=False)
            self.assertEqual(process.returncode,0,process.stderr)
            report=json.loads(process.stdout)
            self.assertEqual(report['schema'],'smartparse.analysis_eligibility')
            self.assertEqual(source.read_bytes(),before)
        finally: source.unlink()


if __name__=='__main__': unittest.main()
