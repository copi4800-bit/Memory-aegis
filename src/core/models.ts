// ============================================================
// Memory Aegis v4 — TypeScript Models
// ============================================================

// --- Taxonomy v1 (Frozen) ---

/**
 * Generic Taxonomy v1 — community-ready labeling.
 * FROZEN: Không thêm/sửa/xóa taxonomy path sau khi freeze.
 * Mọi thay đổi phải qua migration script.
 */
export const TAXONOMY_V1 = {
  "identity.persona": "Thông tin định danh, vai trò, tính cách",
  "identity.style": "Phong cách giao tiếp, ngôn ngữ, tone",
  "policy.safety": "Quy tắc an toàn, ràng buộc bắt buộc, invariant",
  "policy.directive": "Chỉ thị hành vi, hướng dẫn cố định",
  "technical.infra": "Hạ tầng, server, deploy, CI/CD, database",
  "technical.logic": "Logic nghiệp vụ, thuật toán, architecture patterns",
  "technical.tooling": "Công cụ dev: git, docker, npm, terminal, IDE",
  "technical.stack": "Ngôn ngữ & framework: TS, Python, React, Rust",
  "technical.code": "Code snippet, hàm, class, interface",
  "workflow.procedure": "Quy trình, hướng dẫn từng bước, SOP",
  "workflow.decision": "Quyết định đã chốt, lý do, trade-off",
  "context.session": "Ngữ cảnh phiên làm việc, tạm thời",
  "context.project": "Thông tin dự án, timeline, stakeholder",
  "knowledge.fact": "Sự kiện, dữ liệu, observation",
  "knowledge.reference": "Tham chiếu tài liệu, link, nguồn",
  "knowledge.lesson": "Bài học rút ra, post-mortem, retrospective",
} as const;

export type TaxonomyCategory = keyof typeof TAXONOMY_V1;

export const TAXONOMY_CATEGORIES = Object.keys(TAXONOMY_V1) as TaxonomyCategory[];

/**
 * Map từ nhãn cũ (Bowerbird v1) sang nhãn mới (Taxonomy v1).
 */
export const TAXONOMY_MIGRATION_MAP: Record<string, TaxonomyCategory> = {
  "rules.policy": "policy.safety",
  "identity.persona": "identity.persona",
  "workflow.procedure": "workflow.procedure",
  "technical.tooling": "technical.tooling",
  "technical.stack": "technical.stack",
  "technical.architecture": "technical.logic",
  "technical.code_snippet": "technical.code",
};

// --- Enums ---

export type MemoryState = "volatile" | "stable" | "crystallized" | "suppressed" | "archived";
export type NodeStatus = "active" | "expired" | "merged" | "deleted" | "superseded";
export type EdgeStatus = "active" | "weakened" | "pruned";
export type MemorySource = "memory" | "sessions";

export type MemoryType =
  | "identity"
  | "semantic_fact"
  | "episodic"
  | "procedural"
  | "rule"
  | "invariant"
  | "trauma"
  | "working_scratch"
  | "context_texture"
  | "tool_artifact"
  | "correction"
  | "interaction_state"
  | "concept"
  | "derived_rule"
  | "temporal_pattern"
  | "fingerprint"
  | "drift_event";

export type CognitiveLayers =
  | "elephant"
  | "orca"
  | "dolphin"
  | "octopus"
  | "chimpanzee"
  | "sea-lion"
  | "salmon"
  | "nutcracker"
  | "tardigrade"
  | "planarian"
  | "bowerbird"
  | "meerkat"
  | "zebra-finch"
  | "eagle"
  | "scrub-jay"
  | "dragonfly"
  | "weaver-bird"
  | "chameleon";

// --- Core Tables ---

export interface MemoryNode {
  id: string;
  memory_type: MemoryType;
  content: string;
  canonical_subject: string | null;
  scope: string | null;
  tier: string | null;
  status: NodeStatus;
  importance: number;
  salience: number;
  activation_score: number;
  base_decay_rate: number;
  stability_score: number;
  interference_score: number;
  override_priority: number;
  memory_state: MemoryState;
  recall_count: number;
  frequency_count: number;
  reusability_score: number;
  approval_score: number;
  raw_hash: string | null;
  normalized_hash: string | null;
  structure_hash: string | null;
  fingerprint_version: string | null;
  drift_status: string | null;
  ttl_expires_at: string | null;
  created_at: string;
  updated_at: string;
  first_seen_at: string | null;
  last_seen_at: string | null;
  last_access_at: string | null;
  crystallized_at: string | null;
  extension_json: string | null;
  // Episodic Memory (Scrub Jay)
  episode_id: string | null;
  // OpenClaw compatibility fields
  source_path: string | null;
  source_start_line: number | null;
  source_end_line: number | null;
}

export interface Episode {
  id: string;
  parent_id: string | null;
  type: string;
  status: "active" | "concluded" | "summarized";
  goal: string | null;
  context_summary: string | null;
  start_at: string;
  end_at: string | null;
  created_at: string;
}

export interface MemoryEdge {
  id: string;
  src_node_id: string;
  dst_node_id: string;
  edge_type: string;
  weight: number;
  confidence: number;
  scope: string | null;
  tier: string | null;
  status: EdgeStatus;
  coactivation_count: number;
  last_activated_at: string | null;
  created_at: string;
  updated_at: string;
  extension_json: string | null;
}

// --- Identity & Fingerprinting ---

export interface Fingerprint {
  id: string;
  node_id: string;
  raw_hash: string | null;
  normalized_hash: string | null;
  structure_hash: string | null;
  fingerprint_version: string;
  normalization_profile: string | null;
  created_at: string;
}

export interface DriftEvent {
  id: string;
  node_id: string;
  baseline_fingerprint_id: string;
  current_fingerprint_id: string;
  drift_type: string;
  severity: string;
  diff_required: number;
  resolved: number;
  detected_at: string;
  resolved_at: string | null;
  extension_json: string | null;
}

export interface DedupRoute {
  id: string;
  fingerprint_id: string;
  scope: string | null;
  source_event_id: string | null;
  target_node_id: string;
  reuse_action: string;
  created_at: string;
}

// --- Entity & Alias ---

export interface Entity {
  id: string;
  entity_type: string;
  canonical_name: string;
  scope: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  extension_json: string | null;
}

export interface EntityAlias {
  id: string;
  entity_id: string;
  alias_text: string;
  alias_kind: string | null;
  confidence: number;
  created_at: string;
  updated_at: string;
}

// --- Concept & Inference ---

export interface ConceptNode {
  id: string;
  concept_type: string;
  canonical_name: string;
  priority: number;
  override_policy: string | null;
  valid_from: string | null;
  valid_to: string | null;
  confidence: number;
  rule_payload_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConceptInheritance {
  id: string;
  src_kind: string;
  src_id: string;
  dst_kind: string;
  dst_id: string;
  inheritance_type: string;
  priority: number;
  active: number;
  created_at: string;
}

export interface DerivedRelation {
  id: string;
  src_node_id: string;
  dst_node_id: string;
  derivation_type: string;
  derivation_path_json: string;
  derivation_depth: number;
  confidence: number;
  expires_at: string | null;
  created_at: string;
}

// --- Temporal ---

export interface TemporalPattern {
  id: string;
  scope: string | null;
  entity_anchor: string | null;
  pattern_type: string;
  cadence_json: string;
  confidence: number;
  next_expected_at: string | null;
  last_triggered_at: string | null;
  prewarm_policy: string | null;
  suppression_policy: string | null;
  created_at: string;
  updated_at: string;
}

// --- Procedures & Tools ---

export interface Procedure {
  id: string;
  name: string;
  subject: string | null;
  scope: string | null;
  status: string;
  trigger_text: string | null;
  trigger_kind: string | null;
  reusability_score: number;
  approval_score: number;
  created_at: string;
  updated_at: string;
  extension_json: string | null;
}

export interface ProcedureStep {
  id: string;
  procedure_id: string;
  step_index: number;
  step_text: string;
  step_kind: string | null;
  created_at: string;
}

export interface ToolArtifact {
  id: string;
  node_id: string | null;
  artifact_type: string;
  language: string | null;
  entry_command: string | null;
  source_text: string;
  input_contract_json: string | null;
  output_contract_json: string | null;
  sandbox_profile: string | null;
  timeout_policy: string | null;
  approval_required: number;
  reusability_score: number;
  success_count: number;
  failure_count: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

// --- Corrections & Interaction ---

export interface CorrectionTrace {
  id: string;
  scope: string | null;
  context_snapshot: string;
  agent_proposal: string | null;
  user_correction: string;
  final_accepted_form: string | null;
  correction_type: string;
  confidence: number;
  applies_to_json: string | null;
  created_at: string;
  last_reused_at: string | null;
}

export interface InteractionState {
  id: string;
  session_id: string;
  frustration_index: number;
  brevity_preference: number;
  exploration_preference: number;
  correction_pressure: number;
  formality_preference: number;
  last_updated_at: string;
}

// --- Context & Subgraphs ---

export interface ContextTexture {
  id: string;
  name: string;
  scope: string | null;
  tone_profile: string | null;
  format_profile: string | null;
  verbosity_profile: string | null;
  tooling_bias: string | null;
  guardrail_profile: string | null;
  activation_rules_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubgraphPartition {
  id: string;
  name: string;
  scope: string | null;
  partition_type: string;
  activation_policy: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubgraphMembership {
  id: string;
  partition_id: string;
  member_kind: string;
  member_id: string;
  weight: number;
  created_at: string;
}

// --- Events ---

export interface MemoryEvent {
  id: string;
  event_type: string;
  node_id: string | null;
  scope: string | null;
  session_id: string | null;
  payload_json: string | null;
  created_at: string;
}

// --- Telemetry ---

export interface AegisTelemetry {
  db_size_bytes: number;
  wal_size_bytes: number;
  node_count_active: number;
  node_count_superseded: number;
  node_count_archived: number;
  edge_count: number;
  entity_count: number;
  event_count: number;
  dedup_hit_count: number;
  derived_relation_count: number;
  interaction_state_count: number;
  unresolved_contradictions: number;
  latest_backup_at: string | null;
  latest_archive_at: string | null;
  growth_24h_bytes: number;
  growth_7d_bytes: number;
}

// --- Archive ---

export interface ArchiveLog {
  id: string;
  archive_kind: "events" | "nodes";
  file_path: string;
  row_count: number;
  compressed_bytes: number | null;
  checksum: string | null;
  from_timestamp: string;
  to_timestamp: string;
  created_at: string;
}

// --- Schema Version ---

export interface SchemaVersion {
  version: number;
  applied_at: string;
  description: string | null;
}

// --- Config ---

export interface AegisConfig {
  enabledLayers: CognitiveLayers[];
  retrievalMaxHops: number;
  dampingFactor: number;
  decayHalfLifeDays: number;
  crystallizationThreshold: number;
  maintenanceCron: string;
  maxNodesPerSearch: number;
  
  // Viper - Retention & Rotation
  keepDaily?: number;
  keepWeekly?: number;
  keepMonthly?: number;
  maxInteractionStatesPerSession?: number;
  maxScratchCaptureBytes?: number;

  // Leafcutter - Archiving
  archiveEnabled?: boolean;
  archiveAfterDays?: number;
  archiveDir?: string;
}

export const DEFAULT_AEGIS_CONFIG: AegisConfig = {
  enabledLayers: ["elephant", "orca", "salmon", "dolphin", "dragonfly"],
  retrievalMaxHops: 4,
  dampingFactor: 0.5,
  decayHalfLifeDays: 30,
  crystallizationThreshold: 5,
  maintenanceCron: "0 3 * * *",
  maxNodesPerSearch: 50,
  
  // Viper Defaults
  keepDaily: 7,
  keepWeekly: 4,
  keepMonthly: 3,
  maxInteractionStatesPerSession: 10,
  maxScratchCaptureBytes: 1024 * 1024, // 1MB

  // Leafcutter Defaults
  archiveEnabled: true,
  archiveAfterDays: 90,
  archiveDir: "archives",
};

// --- Reranker Weights ---

export interface RerankerWeights {
  fts: number;
  activation: number;
  entity: number;
  retention: number;
  scope: number;
  procedure: number;
  override: number;
  interference_penalty: number;
}

export const DEFAULT_RERANKER_WEIGHTS: RerankerWeights = {
  fts: 0.30,
  activation: 0.25,
  entity: 0.15,
  retention: 0.10,
  scope: 0.10,
  procedure: 0.05,
  override: 2.00,
  interference_penalty: 0.50,
};

// --- Constants ---

export const CONSTANTS = {
  // State transitions
  STABLE_RECALL_THRESHOLD: 3,
  STABLE_STABILITY_THRESHOLD: 0.5,
  STABLE_INTERFERENCE_MAX: 0.3,
  CRYSTALLIZE_RECALL_THRESHOLD: 5,
  CRYSTALLIZE_SPACING_THRESHOLD: 0.6,
  CRYSTALLIZE_INTERFERENCE_MAX: 0.1,
  STABLE_INTERFERENCE_DEMOTE: 0.7,
  VOLATILE_SUPPRESS_THRESHOLD: 0.1,
  REACTIVATE_THRESHOLD: 0.3,
  ARCHIVE_AFTER_DAYS: 90,

  // Spreading activation
  DEFAULT_ACTIVATION_THRESHOLD: 0.05,
  HEBBIAN_INCREMENT: 0.05,

  // Retention
  IMPORTANCE_WEIGHT: 0.6,
  SALIENCE_WEIGHT: 0.4,
  OVERRIDE_WEIGHT: 0.1,
  SPACING_WEIGHT: 1.5,

  // Reranking
  SUPPRESSION_MULTIPLIER: 0.1,

  // Elephant
  ELEPHANT_RELEVANCE_THRESHOLD: 0.2,

  // Edge maintenance
  EDGE_STALE_DAYS: 60,
  EDGE_DECAY_FACTOR: 0.8,
  EDGE_PRUNE_THRESHOLD: 0.01,
  EDGE_PRUNE_MIN_COACTIVATION: 2,

  // Chunking
  MAX_CHUNK_CHARS: 2000,

  // Search
  FTS_CANDIDATE_LIMIT: 100,
  DEFAULT_MAX_RESULTS: 6,
  DEFAULT_MIN_SCORE: 0.35,

  // Inference
  MAX_INHERITANCE_DEPTH: 5,
  INFERENCE_CONFIDENCE_THRESHOLD: 0.3,
  INFERENCE_CONFIDENCE_DECAY: 0.8,

  // Crystallization-eligible types
  CRYSTALLIZATION_ELIGIBLE_TYPES: [
    "procedural", "invariant", "identity", "rule", "trauma",
    "semantic_fact", "concept", "correction",
  ] as MemoryType[],

  // Memory type base strength
  MEMORY_TYPE_STRENGTH: {
    trauma: 0.5,
    invariant: 0.5,
    identity: 0.3,
    procedural: 0.2,
    rule: 0.2,
    semantic_fact: 0.1,
    episodic: 0.0,
    working_scratch: -0.2,
    context_texture: 0.0,
    tool_artifact: 0.1,
    correction: 0.2,
    interaction_state: -0.1,
    concept: 0.2,
    derived_rule: 0.1,
    temporal_pattern: 0.0,
    fingerprint: 0.3,
    drift_event: 0.0,
  } as Record<MemoryType, number>,
} as const;
