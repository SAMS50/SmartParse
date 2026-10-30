// Isolated UI test data only. Production never uses these mocked responses.
import type {Example, StudioResult} from './types/report'
export const examples: Example[] = [
  {id:'valid',title:'Valid C',filename:'valid.c',description:'Valid control',source:'int main(void) { return 0; }\n',source_sha256:'mock',analyzers:['compiler'],recovery:false,isolation:false},
  {id:'null',title:'Null pointer',filename:'null.c',description:'Null example',source:'int read(void) {\n int *p=0;\n return *p;\n}\n',source_sha256:'mock',analyzers:['memory'],recovery:false,isolation:false},
  {id:'recovery',title:'Recovery-assisted',filename:'repair.c',description:'Recovery example',source:'int x=1\nint y=2;\n',source_sha256:'mock',analyzers:['memory'],recovery:true,isolation:false},
]
export function result(conditioning = 'original-source'): StudioResult {
  const conditional = conditioning !== 'original-source'
  return {schema:'smartparse.studio_response',schema_version:'1.0',markdown:'# Actual report summary',studio:{
    request_id:'mock-request',filename:'null.c',submitted_sha256:'mock-source',workspace_removed:true,
    limitations:[],previews:[],editor_locations:{'D-test':{line:3,column:9,precision:'column',reason:'ASCII'}}},
    report:{schema:'smartparse.unified_analysis',schema_version:'1.0',status:'completed',source:{path:'/private/null.c',sha256:'mock-source',original_unchanged:true},
      requested_analyzers:['memory'],effective_analyzers:['memory'],usage:{elapsed_seconds:1.25,compiler_invocations:33},tool_issues:[],
      summary:{errors:0,warnings:1,notes:0,categories:{'memory safety':1},confirmed_defect_roots:null},
      diagnostics:[{id:'D-test',group_id:'G-test',root_id:null,location:{file:'/private/null.c',line:3,column:9},reported_location:{file:'/private/null.c',line:3,column:9},
        location_space:'mapped-original',severity:'warning',category:'memory safety',message:'Dereference of null pointer',analyzer:'Clang Static Analyzer',backend:'clang-static-analyzer',
        diagnostic_id:'core.NullDereference',conditioning,provenance:{repair_conditioned:conditional,isolation_conditioned:false},context_note:false,suggestion:null,
        evidence:{source_snippet:'return *p;',related:[]},raw_record:{message:'Dereference of null pointer'},raw_reference:{run_id:'memory',path:'/findings/0'}}],
      groups:[{id:'G-test',diagnostic_ids:['D-test'],analyzers:['Clang Static Analyzer'],conditioning,basis:'Exact evidence'}],
      runs:[{id:'memory',status:'completed',reason:'Invocation completed; path coverage unknown',elapsed_seconds:1.25,raw:{},usage:{compiler_invocations:33},eligibility:null,
        recovery:conditional ? {stop_reason:'frontend_accepted',candidates:[{id:'C1',status:'accepted',reason:'Machine fix-it and physical AST boundary',fixit:{start_line:1,start_column:8,replacement:';'}}],accepted_variants:[],eligibility_change:{frontend_newly_eligible:true,analyzer_newly_completed:true}} : undefined}]}}
}
