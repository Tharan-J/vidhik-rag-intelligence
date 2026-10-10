/**
 * Vidhik Lawyer Workspace - Data Types
 * Strict Evidence-Centric Verification Architecture
 *
 * PROVENANCE LEVELS:
 * LEVEL 1: Primary Source (Original Court Document / Record)
 * LEVEL 2: Verified Extracted Text (Page/Paragraph Verified)
 * LEVEL 3: Retrieved Evidence (Verbatim Chunks from Indexed Corpus)
 * LEVEL 4: Independently Verified Legal Corpora
 * LEVEL 5: AI Analysis (Clearly identified analytical commentary)
 * LEVEL 6: User Input (Explicitly entered by lawyer)
 */

export type MatterStage =
  | "Filed"
  | "Notice"
  | "Pleadings"
  | "Evidence"
  | "Arguments"
  | "Judgment"
  | "Disposed";

export type FieldProvenanceStatus =
  | "SOURCE_EXPLICIT"
  | "SOURCE_DERIVED"
  | "INDEPENDENTLY_VERIFIED"
  | "AI_ANALYSIS"
  | "USER_PROVIDED"
  | "NOT_FOUND"
  | "NOT_VERIFIED"
  | "CONFLICTING_SOURCE"
  | "FLAGGED_HALLUCINATION";

export type ProvenanceBadgeType =
  | FieldProvenanceStatus
  | "VERIFIED_FROM_SOURCE"
  | "court_explicit"
  | "party_argument"
  | "source_derived"
  | "ai_analysis"
  | "ai_suggestion"
  | "user_specified"
  | "lawyer"
  | "unverified"
  | "flagged_hallucination";

export type VerificationLevel =
  | "LEVEL_1_PRIMARY_SOURCE"
  | "LEVEL_2_VERIFIED_TEXT"
  | "LEVEL_3_RETRIEVED_CHUNKS"
  | "LEVEL_4_INDEPENDENT_CORPUS"
  | "LEVEL_5_AI_ANALYSIS"
  | "LEVEL_6_USER_INPUT";

export type ProceedingType =
  | "ADVERSARIAL"
  | "SUO_MOTU"
  | "IN_RE"
  | "CRIMINAL_APPEAL"
  | "CIVIL_APPEAL"
  | "WRIT"
  | "REVISION"
  | "REFERENCE"
  | "OTHER";

export type TimelineEventType =
  | "FILING"
  | "NOTICE_ISSUED"
  | "HEARING"
  | "INTERIM_ORDER"
  | "ORDER_PASSED"
  | "JUDGMENT_PRONOUNCED"
  | "MATTER_DISPOSED"
  | "DIRECTION_ISSUED"
  | "REPORT_DUE"
  | "PAST_EVENT"
  | "CURRENT_EVENT"
  | "FUTURE_EVENT"
  | "OTHER";

export type SectionApplicability =
  | "SECTION_MENTIONED"
  | "SECTION_APPLIED"
  | "SECTION_HELD_APPLICABLE"
  | "SECTION_ALLEGED_BY_PARTY";

export interface SourceLocation {
  document?: string;
  documentName?: string;
  page?: number | string;
  paragraph?: number | string;
  line?: number | string;
  chunkId?: string;
}

export interface ConflictingSourceItem<T = any> {
  value: T;
  source: string | SourceLocation;
}

export interface ProvenanceField<T> {
  value: T | null;
  provenance: FieldProvenanceStatus;
  source?: SourceLocation;
  conflictingValues?: ConflictingSourceItem<T>[];
  notes?: string;
}

export interface FutureDirectionRef {
  id: string;
  direction: string;
  directedTo?: string;
  timeframe?: string;
  status: "DIRECTED_NOT_COMPLETED" | "COMPLIED" | "PENDING_REPORT";
  source?: SourceLocation;
  provenance: FieldProvenanceStatus;
}

export interface Party {
  role: "Petitioner" | "Respondent" | "Appellant" | "Defendant" | "Plaintiff" | "Intervenor" | "Amicus Curiae";
  name: string;
  counsel?: string;
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  source?: SourceLocation;
}

export interface DocumentMetadata {
  document_type: string;
  case_number?: string;
  court?: string;
  parties?: string[];
  dates?: string[];
  sections?: string[];
  important_points?: string[];
  extraction_source?: string;
  extracted_at?: string;
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
}

export interface MatterDocument {
  id: string;
  matterId: string;
  name: string;
  type: "Pleadings" | "Orders" | "Judgments" | "Applications" | "Evidence" | "Other";
  date: string;
  pages: number;
  uploadedAt: string;
  status: "active" | "archived";
  fileSize?: string;
  extractionStatus: "pending" | "completed" | "failed";
  extractedMetadata?: DocumentMetadata;
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  sourceLocation?: SourceLocation;
  storagePath?: string;
  sha256?: string;
}

export interface TimelineEvent {
  id: string;
  matterId: string;
  date: string;
  title: string;
  description?: string;
  sourceDocumentId?: string;
  sourceDocumentName?: string;
  source?: "court_record" | "lawyer" | "ai_extraction";
  courtStage?: MatterStage;
  eventType?: TimelineEventType;
  page?: string;
  paragraph?: string;
  sourceLocation?: SourceLocation;
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  status?: "COMPLETED" | "DIRECTED_NOT_COMPLETED" | "PENDING";
  conflictingDates?: ConflictingSourceItem<string>[];
}

export interface MatterIssue {
  id: string;
  matterId: string;
  issueNumber: string;
  title: string;
  description?: string;
  source: "court_explicit" | "party_argument" | "source_derived" | "ai_analysis" | "lawyer" | "ai_suggestion";
  confirmed: boolean;
  relatedDocuments: string[];
  relatedSections: string[];
  relatedAuthorities: string[];
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  verification?: "explicit" | "unverified" | "ai_derived";
  issueCategory?: "FACTUAL_BACKGROUND" | "LOWER_COURT_FINDING" | "PARTY_ARGUMENT" | "LEGAL_TEST" | "COURT_REASONING" | "FINAL_HOLDING" | "DIRECTIONS";
  sourceLocation?: SourceLocation;
}

export interface SectionRef {
  id: string;
  act: string;
  section: string;
  heading?: string | null;
  headingVerification?: "VERIFIED" | "NOT_VERIFIED";
  applicability?: SectionApplicability;
  description: string;
  context?: string;
  sourceDocument: string;
  page?: string;
  paragraph?: string;
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  sourceLocation?: SourceLocation;
}

export interface AuthorityRef {
  id: string;
  caseTitle: string;
  caseNumber: string;
  court: string;
  year: string;
  relevance: string;
  supportingEvidence: string;
  evidenceId?: string;
  page?: string;
  paragraph?: string;
  sourceFile?: string;
  presence?: "FOUND_IN_SOURCE" | "EXTERNAL_REFERENCE";
  independentVerification?: "VERIFIED" | "NOT_VERIFIED" | "NOT_PERFORMED" | "FLAGGED_HALLUCINATION";
  propositionSupport?: "SUPPORTED" | "NOT_SUPPORTED" | "UNCHECKED";
  authorityStatus?: "VERIFIED_AUTHORITY" | "UNVERIFIED_AUTHORITY" | "FLAGGED_FAKE";
  verificationStatus?: "verified_in_judgment" | "unverified" | "flagged_hallucination";
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  sourceLocation?: SourceLocation;
}

export interface MatterNote {
  id: string;
  matterId: string;
  title: string;
  content: string;
  updatedAt?: string;
  createdAt?: string;
  tags?: string[];
  noteType?: "SOURCE_FACT" | "SOURCE_DERIVED" | "AI_ANALYSIS" | "USER_NOTE";
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  sourceLocation?: SourceLocation;
}

export interface MatterEvidenceItem {
  id: string;
  matterId: string;
  issueId: string;
  issueTitle: string;
  claim: string;
  claimType?: "FACTUAL_BACKGROUND" | "LOWER_COURT_FINDING" | "PARTY_ARGUMENT" | "LEGAL_TEST" | "COURT_REASONING" | "FINAL_HOLDING" | "DIRECTIONS";
  status?: "SUPPORTED" | "UNSUPPORTED" | "INSUFFICIENT_EVIDENCE";
  stance: "supporting" | "contradicting";
  evidenceExcerpt: string;
  sourceDocument: string;
  pageNumber?: string;
  paragraphId?: string;
  sourceType?: "PRIMARY_JUDGMENT" | "REPORTED_PRECEDENT" | "PLEADINGS" | "STATUTE";
  relatedAuthority?: {
    caseTitle: string;
    court: string;
    year: string;
    citation?: string;
  };
  isPinned?: boolean;
  notes?: string[];
  confidence?: string;
  isCustom?: boolean;
  rawSourceText?: string;
  grounded?: boolean;
  verification?: "source_supported" | "unverified" | "insufficient_evidence";
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  sourceLevel?: VerificationLevel;
  sourceLocation?: SourceLocation;
}

export interface Matter {
  id: string;
  title: string;
  caseNumber: string;
  neutralCitation?: string;
  court: string;
  matterType: string;
  proceedingType?: ProceedingType;
  proceedingStyle?: string;
  subject?: string;
  participants?: string[];
  status: MatterStage;
  currentStage: string;
  createdAt: string;
  updatedAt: string;
  lastKnownEvent: string;
  nextImportantEvent: string;
  client: string;
  summary: string;
  sourceSummary?: string;
  sourceDerivedSummary?: string;
  aiAnalysis?: string;
  provenance?: FieldProvenanceStatus | ProvenanceBadgeType;
  fieldProvenance?: {
    court?: ProvenanceField<string>;
    caseNumber?: ProvenanceField<string>;
    judgmentDate?: ProvenanceField<string>;
    filingDate?: ProvenanceField<string>;
    proceedingType?: ProvenanceField<string>;
    client?: ProvenanceField<string>;
    status?: ProvenanceField<string>;
    summary?: ProvenanceField<string>;
  };
  futureDirections?: FutureDirectionRef[];
  aiSummary?: {
    summary: string;
    current_status: string;
    important_dates: { label: string; date: string; source: string }[];
    key_issues: string[];
    documents_requiring_attention: string[];
    generated_at: string;
    originating_documents: string[];
  };
  parties: {
    petitioner?: string;
    respondent?: string;
    counsel?: string;
    court?: string;
    bench?: string;
  };
  importantDates: {
    filingDate: string;
    lastHearing: string;
    nextHearing?: string;
    judgmentDate?: string;
    writtenSubmissionsDeadline?: string;
  };
  documents: MatterDocument[];
  timeline: TimelineEvent[];
  issues: MatterIssue[];
  sections: SectionRef[];
  authorities: AuthorityRef[];
  notes: MatterNote[];
  evidence?: MatterEvidenceItem[];
}

export interface RecentActivity {
  id: string;
  matterId: string;
  matterTitle: string;
  type: "document_added" | "issue_identified" | "research_saved" | "hearing_updated" | "note_created";
  title: string;
  detail: string;
  timestamp: string;
}

export interface UpcomingItem {
  id: string;
  matterId: string;
  matterTitle: string;
  title: string;
  date: string;
  type: "hearing" | "deadline" | "submission";
  court: string;
}
