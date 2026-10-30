"""Independent invariants for the eligibility envelope, not completeness proof."""
import re


def validate_eligibility(report):
    def require(condition,message):
        if not condition: raise ValueError(message)
    required={'schema','schema_version','manifest','stages','blockers','region_inventory','regions','mapping','analysis'}
    require(isinstance(report,dict) and required<=report.keys(),'missing envelope fields')
    require(report['schema']=='smartparse.analysis_eligibility' and report['schema_version']=='1.0','unknown schema')
    source=report['manifest']['source']
    require(isinstance(source['path'],str),'invalid source path')
    require(source['sha256'] is None or re.fullmatch('[0-9a-f]{64}',source['sha256']) is not None,'invalid source hash')
    require(report['mapping']['source_edits_applied'] is False,'this milestone must never edit source')
    require(report['stages']['compiler']['completion']==report['analysis']['status'],'compiler completion mismatch')
    expected=report['analysis'].get('static_analysis',{}).get('status','not_attempted')
    require(report['stages']['analyzer']['completion']==expected,'analyzer completion mismatch')
    allowed={'preprocessing/configuration','syntax','semantic/type','timeout','analyzer limitations'}
    for blocker in report['blockers']:
        require(blocker['category'] in allowed and isinstance(blocker['message'],str),'invalid blocker')
    require(isinstance(report['regions'],list) and bool(report['regions']),'missing translation unit')
    ids=set()
    for region in report['regions']:
        require(region['id'] not in ids,'duplicate region'); ids.add(region['id'])
        require(region['kind'] in ('translation_unit','function'),'invalid region kind')
        for key in ('compiler_coverage','analyzer_coverage'):
            require(region[key]['status'] in ('completed','blocked','not_attempted','unknown'),'invalid coverage')
            require(isinstance(region[key]['reason'],str) and bool(region[key]['reason']),'missing coverage reason')
        # This implementation has no analyzer exploration certificate.
        require(region['analyzer_coverage']['status']!='completed','unjustified analyzer region coverage')
        if region['compiler_coverage']['status']=='completed':
            require(report['stages']['compiler']['frontend_accepted'] is True,'rejected frontend cannot certify a region')
            require(source['original_source_unchanged'] is True,'changed source cannot certify coverage')
        if region['kind']=='function':
            require(region['reliability']=='validated_ast_range','unverified function boundary')
            require(type(region['start_byte']) is int and 0<=region['start_byte']<region['end_byte_exclusive']<=source['bytes'],'invalid physical range')
            require(1<=region['start_line']<=region['end_line']<=source['physical_lines'],'invalid physical line')
            if region['compiler_coverage']['status']=='completed':
                require(report['region_inventory']['status']=='completed','partial inventory cannot certify frontend body')
    return True
