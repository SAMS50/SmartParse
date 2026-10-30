"""Checkout an isolated Git tree; never stage/commit in the real repository."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from .release import ROOT,payload,verify,git
from .validate import OUT,write
from phase6.v3.supervision import run_logged


def main():
    p=argparse.ArgumentParser();p.add_argument('--no-suite',action='store_true',help='only lightweight final-payload recheck');a=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    index=ROOT/'.git/index';index_before=hashlib.sha256(index.read_bytes()).hexdigest()
    entries_before=git('ls-files','--stage','-z')
    head=git('rev-parse','HEAD').decode().strip();names=payload()
    tracked=set(git('ls-files','-z').decode().strip('\0').split('\0'))
    modified=set(git('diff','--name-only','-z').decode().strip('\0').split('\0'))
    additions=sorted(n for n in names if n not in tracked or n in modified)
    record=dict(source_head=head,commits_created=False,real_index_unchanged=None,checkouts=[])
    with tempfile.TemporaryDirectory(prefix='smartparse-release-checkout-') as scratch:
        store=Path(scratch)/'object-store';store.mkdir()
        subprocess.run(['git','init','--quiet',str(store)],check=True,timeout=30)
        private_git=store/'.git'
        (private_git/'objects/info/alternates').write_bytes(((ROOT/'.git/objects').as_posix()+'\n').encode('utf-8'))
        def isolated(*args,work=ROOT,data=None):
            process=subprocess.run(['git','--git-dir='+str(private_git),'--work-tree='+str(work),*args],
                input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,shell=False)
            if process.returncode:raise RuntimeError('Isolated Git '+args[0]+': '+process.stderr.decode('utf-8',errors='replace'))
            return process.stdout
        isolated('config','core.autocrlf','true')
        isolated('read-tree',head)
        isolated('add','--pathspec-from-file=-','--pathspec-file-nul',data=b'\0'.join(n.encode() for n in additions)+b'\0')
        tree=isolated('write-tree').decode().strip();record['tree']=tree
        paths=set(isolated('ls-tree','-r','--name-only','-z',tree).decode().strip('\0').split('\0'))
        if paths!=set(names):raise RuntimeError('Isolated tree membership differs from approved payload')
        record['payload_files']=len(paths)
        env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
        from smartparse_cli.tools import locate
        clang=locate('clang')
        if clang:env['PATH']=str(Path(clang).parent)+os.pathsep+env.get('PATH','')
        sealed=[]
        # Materialize both snapshots before running user-facing commands/tests.
        # No late Git reconfiguration is needed after a long regression run.
        for mode in ('true','false'):
            checkout=Path(scratch)/('checkout-autocrlf-'+mode);checkout.mkdir()
            isolated('config','core.autocrlf',mode)
            isolated('checkout-index','--all','--force',work=checkout)
            outcome=dict(core_autocrlf=mode,manifest=verify(checkout),commands=[])
            local_only=['acceptance/output/broken_records.json','phase6/v8/outputs/extended/compiler_clang/C01_null.log']
            outcome['excluded_local_artifacts_absent']=all(not (checkout/n).exists() for n in local_only)
            if not outcome['excluded_local_artifacts_absent']:raise RuntimeError('Local-only evidence unexpectedly copied into checkout')
            if not outcome['manifest']['preserved']:raise RuntimeError('Checkout byte/content integrity failed: '+str(outcome['manifest']))
            for name in ('phase6/v8/fixtures/c/C01_null.c','phase6/v8/manifest.json','baseline.py','smartparse.py'):
                data=(checkout/name).read_bytes()
                entry=isolated('show',':'+name)
                outcome.setdefault('representative_bytes',[]).append(dict(path=name,
                    blob_sha256=hashlib.sha256(entry).hexdigest(),working_sha256=hashlib.sha256(data).hexdigest(),
                    working_crlf=data.count(b'\r\n'),working_lf=data.count(b'\n')))
            sealed.append((mode,checkout,outcome))
        for mode,checkout,outcome in sealed:
            cases=[('version',['-m','smartparse_cli','--version'],0),
                   ('doctor',['-m','smartparse_cli','doctor'],0),
                   ('valid',['-m','smartparse_cli','analyze','phase6/v8/fixtures/c/C12_valid_full.c'],0)]
            if a.no_suite:
                cases.append(('compatibility',['-m','unittest','test_release_reproducibility','test_smartparse_cli',
                    'phase6.v1.test_evaluation.EvidenceModelTests.test_saved_assisted_review_remains_auditable',
                    'phase6.v5.test_detection.PolicyTests','-v'],0))
            if mode=='true' and not a.no_suite:cases.append(('full_suite',['-m','unittest','discover','-v'],0))
            before={p:p.read_bytes() for p in (checkout/'results').rglob('*.csv')}
            try:
                for label,args,expected in cases:
                    log=OUT/(mode+'-'+label+'.log')
                    result=run_logged([sys.executable,*args],log,timeout=600 if label=='full_suite' else 45,env=env,cwd=checkout)
                    result.update(name=label,expected_exit=expected,passed=result['exit_code']==expected and not result['timed_out'])
                    outcome['commands'].append(result)
                    print(mode,label,result['exit_code'],result['passed'],flush=True)
            finally:
                restored=[]
                for path,data in before.items():
                    if path.read_bytes()!=data:path.write_bytes(data);restored.append(path.relative_to(checkout).as_posix())
                outcome['legacy_csv_bytes_restored']=restored
            outcome['post_validation']=verify(checkout)
            outcome['passed']=all(c['passed'] for c in outcome['commands']) and outcome['post_validation']['preserved']
            record['checkouts'].append(outcome);write('fresh_checkout.json',record)
        record['private_git_metadata_after_tests']={name:(private_git/name).is_file() for name in ('HEAD','config','index')}
    record['real_index_byte_cache_unchanged']=hashlib.sha256(index.read_bytes()).hexdigest()==index_before
    record['real_index_unchanged']=git('ls-files','--stage','-z')==entries_before
    record['index_check_basis']='Exact staged modes/object IDs/stages/paths; byte-cache hash recorded separately because Git/IDE stat refreshes are not staging.'
    record['passed']=record['real_index_unchanged'] and all(c['passed'] for c in record['checkouts'])
    write('fresh_checkout.json',record)
    return 0 if record['passed'] else 1


if __name__=='__main__':sys.exit(main())
