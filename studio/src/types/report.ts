export type AnalysisStatus = 'completed' | 'partial' | 'failed' | string
export interface Location {file: string | null; line: number | null; column: number | null}
export interface Diagnostic {
  id: string; group_id: string; root_id: string | null; location: Location; reported_location: Location;
  location_space: string; severity: string | null; category: string; message: string;
  analyzer: string; backend: string; diagnostic_id: string | null; conditioning: string;
  provenance: Record<string, unknown>; context_note: boolean; suggestion: unknown;
  evidence: {source_snippet: string | null; related: unknown[]};
  raw_record: Record<string, unknown>; raw_reference: {run_id: string; path: string};
}
export interface Candidate {
  id: string; status: string; reason: string; round?: number;
  fixit?: {start_line: number; start_column: number; end_line?: number; end_column?: number; replacement: string; diagnostic?: {message: string}};
  score?: number;
}
export interface Run {
  id: string; status: AnalysisStatus; reason: string | null; elapsed_seconds: number;
  raw: Record<string, unknown>; usage: {compiler_invocations?: number}; eligibility: unknown;
  recovery?: {stop_reason: string; candidates: Candidate[]; accepted_variants: unknown[]; eligibility_change: Record<string, unknown>};
  isolation?: {status: string; reason: string; excluded_functions: unknown[]; eligibility_improved: boolean};
}
export interface Group {id: string; diagnostic_ids: string[]; analyzers: string[]; conditioning: string; basis: string}
export interface Report {
  intent_recovery?: IntentRecovery;
  schema: 'smartparse.unified_analysis'; schema_version: '1.0'; status: AnalysisStatus;
  source: {path: string; sha256: string; original_unchanged: boolean};
  requested_analyzers: string[]; effective_analyzers: string[]; diagnostics: Diagnostic[]; groups: Group[]; runs: Run[];
  summary: {errors: number; warnings: number; notes: number; categories: Record<string, number>; confirmed_defect_roots: null};
  usage: {elapsed_seconds: number; compiler_invocations: number};
  tool_issues: {analyzer: string; status: string; message: string}[];
  [key: string]: unknown;
}
export interface EditorLocation {line: number; column: number; precision: 'line' | 'column'; reason: string}
export interface Preview {run_id: string; variant_id: string; source: string; sha256: string; conditioning: string; basis: string}
export interface StudioResult {
  schema: 'smartparse.studio_response'; schema_version: '1.0'; report: Report; markdown: string;
  studio: {request_id: string; filename: string; submitted_sha256: string; editor_locations: Record<string, EditorLocation>;
    previews: Preview[]; workspace_removed: boolean; limitations: string[]};
}
export interface Example {id: string; title: string; filename: string; description: string; source: string; source_sha256: string; analyzers: string[]; recovery: boolean; isolation: boolean}
export interface Tool {name: string; path: string | null; status: string; version: string | null; reason?: string}
export interface Settings {analyzers: string[]; recovery: boolean; isolation: boolean; standard: string; intent_recovery?:boolean}
export interface AnalysisInput extends Settings {source: string; filename: string;edit_history?:import('../lib/editHistory').EditHistory;intent_version?:'v11'|'v12'|'v14'}
export interface IntentCandidate {
  id:string;source:string;status:string;score:number;explanation:string;
  changes:{offset:number;end_offset:number;deleted:string;inserted:string;line:number;column:number}[];
  validation:{status:string;reason:string};history:{explanation:string};
  semantic:Record<string,{status:string;explanation:string}>;
  origin?:string;origins?:string[];semantic_risk?:{status:string;reason:string};
}
export interface IntentRecovery {decision:string;reason:string;recommendation:string|null;history_status:string;original_sha256:string;candidates:IntentCandidate[];
  algorithm?:string;evidence_basis?:string;decision_mode?:string;outcome?:string;available_evidence?:string[];missing_evidence?:string[];
  reliability?:{status:string;intent_support:string;reason:string;mapping_verified:boolean}}
