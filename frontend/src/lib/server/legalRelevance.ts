import fs from "fs";
import path from "path";
import { Matter } from "@/lib/types/matter";

export interface QueryTargets {
  rawQuery: string;
  articles: string[];
  sections: string[];
  acts: string[];
  concepts: string[];
  hasExplicitStatutoryTargets: boolean;
  allTargets: string[];
}

export interface ValidatedEvidenceHit {
  evidence_id: string;
  document_id: string;
  chunk_id: string;
  score: number;
  court: string;
  case_title: string;
  case_number?: string;
  neutral_citation?: string;
  page_number?: string | number;
  paragraph_id?: string | number;
  text: string;
  relevantExcerpt: string;
  target_matches: string[];
  isRelevant: boolean;
  relevanceReason: string;
  relevanceCategory?: "DIRECT_EVIDENCE" | "SUPPORTING_CONTEXT" | "CONTRARY_OR_QUALIFYING" | "IRRELEVANT" | "INSUFFICIENT";
}

export interface RejectedAuthority {
  document_id: string;
  case_title: string;
  court: string;
  reason: string;
  detectedProvisions: string[];
}

const EXTRACTED_MATTERS_PATH = path.resolve(
  process.cwd(),
  "src",
  "lib",
  "data",
  "extracted_matters.json"
);

/**
 * 1. Extract explicit legal targets from the user query
 * e.g., "get me the court case related to Articles 14, 15, 16" -> ["Article 14", "Article 15", "Article 16"]
 */
export function extractQueryTargets(query: string): QueryTargets {
  const normalized = query.trim();
  const articles: string[] = [];
  const sections: string[] = [];
  const acts: string[] = [];
  const concepts: string[] = [];

  // 1. Constitutional Articles detection (handling lists like "Articles 14, 15, 16", "Articles 14, 15 and 16", "Article 20(1)", "Article 368")
  const articleListRegex = /\barticles?\s+((?:\d+(?:\([A-Za-z0-9]+\))*(?:\s*,\s*|\s+and\s+|\s*&\s*|\s+to\s+|-)?)+)/gi;
  let artMatch: RegExpExecArray | null;
  while ((artMatch = articleListRegex.exec(normalized)) !== null) {
    const listPart = artMatch[1];
    // Check for range like "14 to 18" or "14-18"
    const rangeM = listPart.match(/^(\d+)\s*(?:to|-)\s*(\d+)$/i);
    if (rangeM) {
      const start = parseInt(rangeM[1], 10);
      const end = parseInt(rangeM[2], 10);
      for (let i = start; i <= end; i++) {
        const artName = `Article ${i}`;
        if (!articles.includes(artName)) articles.push(artName);
      }
    } else {
      const numbers = listPart.match(/\d+(?:\([A-Za-z0-9]+\))*/g) || [];
      for (const num of numbers) {
        const artName = `Article ${num}`;
        if (!articles.includes(artName)) {
          articles.push(artName);
        }
      }
    }
  }

  // 2. Statutory Sections detection (e.g. "Section 156(3)", "Section 376", "Sections 7 and 14", "Section 498A")
  const sectionListRegex = /\bsections?\s+((?:\d+[A-Za-z]*(?:\([A-Za-z0-9]+\))*(?:\s*,\s*|\s+and\s+|\s*&\s*|\s+to\s+|-)?)+)/gi;
  let secMatch: RegExpExecArray | null;
  while ((secMatch = sectionListRegex.exec(normalized)) !== null) {
    const listPart = secMatch[1];
    const numbers = listPart.match(/\d+[A-Za-z]*(?:\([A-Za-z0-9]+\))*/g) || [];
    for (const num of numbers) {
      const secName = `Section ${num}`;
      if (!sections.includes(secName)) {
        sections.push(secName);
      }
    }
  }

  // 3. Known Acts detection
  const actKeywords: Record<string, string> = {
    constitution: "Constitution of India",
    crpc: "Code of Criminal Procedure, 1973",
    ipc: "Indian Penal Code, 1860",
    pocso: "POCSO Act, 2012",
    ibc: "Insolvency and Bankruptcy Code, 2016",
    "insolvency and bankruptcy": "Insolvency and Bankruptcy Code, 2016",
    arbitration: "Arbitration & Conciliation Act, 1996",
    limitation: "Limitation Act, 1963",
    "companies act": "Companies Act, 2013",
    "negotiable instruments": "Negotiable Instruments Act, 1881",
  };

  const lowerQ = normalized.toLowerCase();
  for (const [key, fullName] of Object.entries(actKeywords)) {
    if (lowerQ.includes(key) && !acts.includes(fullName)) {
      acts.push(fullName);
    }
  }

  // 4. Key legal concepts
  const conceptKeywords = [
    "preamble",
    "secular",
    "socialist",
    "equality",
    "condonation of delay",
    "sufficient cause",
    "attempt",
    "preparation",
    "corporate debtor",
    "personal guarantor",
    "moratorium",
    "quashing",
    "anticipatory bail",
  ];

  for (const kw of conceptKeywords) {
    if (lowerQ.includes(kw) && !concepts.includes(kw)) {
      concepts.push(kw);
    }
  }

  const allTargets = [...articles, ...sections, ...acts, ...concepts];
  const hasExplicitStatutoryTargets = articles.length > 0 || sections.length > 0;

  return {
    rawQuery: normalized,
    articles,
    sections,
    acts,
    concepts,
    hasExplicitStatutoryTargets,
    allTargets,
  };
}

/**
 * Robust check whether a legal target is mentioned or substantively discussed in text
 */
export function matchesProvisionOrTarget(target: string, text: string): boolean {
  if (!target || !text) return false;
  const lowerText = text.toLowerCase();
  const lowerTarget = target.toLowerCase();

  // 1. Direct word-boundary match (not arbitrary substring to prevent "Section 37" matching "Section 376")
  const escaped = lowerTarget.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const wordBoundaryRegex = new RegExp(`\\b${escaped}\\b`, "i");
  if (wordBoundaryRegex.test(text)) return true;

  // 2. Constitutional Article check (e.g. target "Article 14", "Article 15", "Article 16", "Article 20(1)")
  const artTargetMatch = target.match(/^article\s+(\d+)(?:\(([0-9A-Za-z]+)\))?/i);
  if (artTargetMatch) {
    const artNum = parseInt(artTargetMatch[1], 10);
    const subClause = artTargetMatch[2];

    // Proximity regex: match "Articles? ... 14" (e.g. "Articles 14, 15, and 16", "Article 14(1)", "Art. 14")
    const listPattern = new RegExp(
      `\\barticles?\\b[^.;\\n]{0,100}\\b${artNum}(?:\\(${subClause || "[0-9A-Za-z]+"}\\))?\\b`,
      "i"
    );
    if (listPattern.test(text)) return true;

    const shortPattern = new RegExp(
      `\\bart\\.?\\s*[^.;\\n]{0,60}\\b${artNum}(?:\\(${subClause || "[0-9A-Za-z]+"}\\))?\\b`,
      "i"
    );
    if (shortPattern.test(text)) return true;

    // Range regex: e.g. "Articles 14 to 18", "Articles 12 to 35", "Articles 14-17"
    const rangePattern = /\barticles?\s+(\d+)\s*(?:to|-|through)\s*(\d+)\b/gi;
    let rMatch: RegExpExecArray | null;
    while ((rMatch = rangePattern.exec(text)) !== null) {
      const start = parseInt(rMatch[1], 10);
      const end = parseInt(rMatch[2], 10);
      if (artNum >= start && artNum <= end) {
        return true;
      }
    }
  }

  // 3. Statutory Section check (e.g. target "Section 156(3)", "Section 498A", "Section 34")
  const secTargetMatch = target.match(/^section\s+(\d+[A-Za-z]*)(?:\(([0-9A-Za-z]+)\))?/i);
  if (secTargetMatch) {
    const secNum = secTargetMatch[1];
    const secClause = secTargetMatch[2];
    const escapedSec = secNum.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

    const secPattern = new RegExp(
      `\\bsections?\\b[^.;\\n]{0,100}\\b${escapedSec}(?:\\(${secClause || "[0-9A-Za-z]+"}\\))?\\b`,
      "i"
    );
    if (secPattern.test(text)) return true;

    const shortPattern = new RegExp(
      `\\bsec\\.?\\s*[^.;\\n]{0,60}\\b${escapedSec}(?:\\(${secClause || "[0-9A-Za-z]+"}\\))?\\b`,
      "i"
    );
    if (shortPattern.test(text)) return true;
  }

  return false;
}

/**
 * Extract provisions mentioned in a text chunk for provenance & rejection reporting
 */
export function extractProvisionsFromText(text: string): string[] {
  const provisions: string[] = [];
  if (!text) return provisions;

  // Article matches: e.g. "Article 20(1)", "Article 368", "Articles 14, 15, and 16"
  const artRegex = /\barticles?\s+((?:\d+(?:\([A-Za-z0-9]+\))*(?:\s*,\s*|\s+and\s+|\s*&\s*|\s+to\s+|-)?)+)/gi;
  let artMatch: RegExpExecArray | null;
  while ((artMatch = artRegex.exec(text)) !== null) {
    const listPart = artMatch[1];
    const numbers = listPart.match(/\d+(?:\([A-Za-z0-9]+\))*/g) || [];
    for (const num of numbers) {
      const artName = `Article ${num}`;
      if (!provisions.includes(artName)) {
        provisions.push(artName);
      }
    }
  }

  // Section matches: e.g. "Section 156(3)", "Section 376", "Section 498A"
  const secRegex = /\bsections?\s+((?:\d+[A-Za-z]*(?:\([A-Za-z0-9]+\))*(?:\s*,\s*|\s+and\s+|\s*&\s*|\s+to\s+|-)?)+)/gi;
  let secMatch: RegExpExecArray | null;
  while ((secMatch = secRegex.exec(text)) !== null) {
    const listPart = secMatch[1];
    const numbers = listPart.match(/\d+[A-Za-z]*(?:\([A-Za-z0-9]+\))*/g) || [];
    for (const num of numbers) {
      const secName = `Section ${num}`;
      if (!provisions.includes(secName)) {
        provisions.push(secName);
      }
    }
  }

  return provisions;
}

/**
 * 2. Search verified matter records in extracted_matters.json for direct target matches
 */
export function searchExtractedMattersForTargets(
  targets: QueryTargets
): ValidatedEvidenceHit[] {
  if (!fs.existsSync(EXTRACTED_MATTERS_PATH)) return [];

  let matters: Matter[] = [];
  try {
    matters = JSON.parse(fs.readFileSync(EXTRACTED_MATTERS_PATH, "utf-8"));
  } catch {
    return [];
  }

  const hits: ValidatedEvidenceHit[] = [];

  for (const m of matters) {
    const matchedTargets: string[] = [];

    // Check sections
    const matchingSections = (m.sections || []).filter((s) => {
      // If query specified an explicit Act, verify the section belongs to a matching Act
      if (targets.acts.length > 0) {
        const actMatches = targets.acts.some(
          (act) =>
            s.act.toLowerCase().includes(act.toLowerCase()) ||
            act.toLowerCase().includes(s.act.toLowerCase())
        );
        if (!actMatches) return false;
      }
      const secBlob = `${s.act} ${s.section} ${s.heading || ""} ${s.description}`;
      return targets.allTargets.some((t) => {
        if (matchesProvisionOrTarget(t, secBlob)) {
          if (!matchedTargets.includes(t)) matchedTargets.push(t);
          return true;
        }
        return false;
      });
    });

    // Check evidence items
    const matchingEvidence = (m.evidence || []).filter((ev) => {
      const evBlob = `${ev.claim} ${ev.evidenceExcerpt} ${ev.issueTitle}`;
      return targets.allTargets.some((t) => {
        if (matchesProvisionOrTarget(t, evBlob)) {
          if (!matchedTargets.includes(t)) matchedTargets.push(t);
          return true;
        }
        return false;
      });
    });

    // Check document metadata sections
    for (const doc of m.documents || []) {
      const metaSecs = doc.extractedMetadata?.sections || [];
      for (const ms of metaSecs) {
        for (const t of targets.allTargets) {
          if (matchesProvisionOrTarget(t, ms) && !matchedTargets.includes(t)) {
            matchedTargets.push(t);
          }
        }
      }
    }

    // Determine if this matter is genuinely relevant to the targets
    if (targets.hasExplicitStatutoryTargets) {
      const hasStatutoryMatch =
        targets.articles.some((a) => matchedTargets.includes(a)) ||
        targets.sections.some((s) => matchedTargets.includes(s));
      if (!hasStatutoryMatch) continue;
    } else if (matchedTargets.length === 0) {
      continue;
    }

    // Build evidence hits from verified matter evidence & sections
    const primaryDoc = m.documents?.[0]?.name || `${m.title}.pdf`;

    if (matchingSections.length > 0) {
      for (const s of matchingSections) {
        hits.push({
          evidence_id: `MATTER-${m.id}-${s.id}`,
          document_id: primaryDoc,
          chunk_id: s.section,
          score: 1.0,
          court: m.court,
          case_title: m.title,
          case_number: m.caseNumber,
          neutral_citation: m.neutralCitation,
          page_number: s.page || "Page 3",
          paragraph_id: "Para 3",
          text: `${s.act} - ${s.section}: ${s.heading ? s.heading + " - " : ""}${s.description}`,
          relevantExcerpt: `${s.section}: ${s.description}`,
          target_matches: matchedTargets,
          isRelevant: true,
          relevanceReason: `Verified statutory provision in matter: ${s.section}`,
        });
      }
    }

    if (matchingEvidence.length > 0) {
      for (const ev of matchingEvidence) {
        hits.push({
          evidence_id: `MATTER-${m.id}-${ev.id}`,
          document_id: primaryDoc,
          chunk_id: ev.paragraphId || "Para",
          score: 0.95,
          court: m.court,
          case_title: m.title,
          case_number: m.caseNumber,
          neutral_citation: m.neutralCitation,
          page_number: ev.pageNumber || "Page Record",
          paragraph_id: ev.paragraphId || "Para Record",
          text: ev.evidenceExcerpt,
          relevantExcerpt: ev.evidenceExcerpt,
          target_matches: matchedTargets,
          isRelevant: true,
          relevanceReason: `Verified primary matter evidence discussing ${matchedTargets.join(", ")}`,
        });
      }
    }
  }

  return hits;
}

/**
 * 3. Validate candidate hits against explicit query targets.
 * Distinguishes document retrieval from query relevance.
 * Rejects documents that do not discuss or apply target provisions.
 */
export function validateCandidateHit(
  hit: {
    evidence_id: string;
    document_id: string;
    chunk_id: string;
    score: number;
    court: string;
    case_title: string;
    text: string;
  },
  targets: QueryTargets
): {
  isRelevant: boolean;
  relevanceReason: string;
  relevanceCategory?: "DIRECT_EVIDENCE" | "SUPPORTING_CONTEXT" | "CONTRARY_OR_QUALIFYING" | "IRRELEVANT" | "INSUFFICIENT";
  targetMatches: string[];
  relevantExcerpt: string;
  detectedProvisions: string[];
  page_number?: string;
  paragraph_id?: string;
} {
  const text = hit.text || "";
  const lowerText = text.toLowerCase();
  const lowerTitle = (hit.case_title || "").toLowerCase();
  const fullText = `${lowerTitle}\n${lowerText}`;

  // Detect which provisions this chunk actually discusses
  const detectedProvisions = extractProvisionsFromText(text);

  // Extract page or paragraph coordinates if present in text
  let page_number: string | undefined;
  let paragraph_id: string | undefined;

  const pageRegex = /(?:Page\s+(?:of\s+)?(\d+)|---\s*PAGE\s+(\d+)\s*---|\[\d+\]\s*\d*\s*S\.C\.R\.\s*(\d+)|\b(\d+)\s+SUPREME COURT REPORTS)/i;
  const pageM = text.match(pageRegex);
  if (pageM) {
    page_number = `Page ${pageM[1] || pageM[2] || pageM[3] || pageM[4]}`;
  }

  const paraRegex = /(?:Para(?:graph)?\s*(\d+)|\b(\d+)\.\s+[A-Z]|Question No\.\s*(\d+))/i;
  const paraM = text.match(paraRegex);
  if (paraM) {
    paragraph_id = `Para ${paraM[1] || paraM[2] || paraM[3]}`;
  }

  // A. If query has explicit statutory targets (e.g. Articles 14, 15, 16):
  if (targets.hasExplicitStatutoryTargets) {
    const matchedArticles: string[] = [];
    const matchedSections: string[] = [];

    // Check for article mentions or direct semantic application
    for (const art of targets.articles) {
      if (matchesProvisionOrTarget(art, text) || matchesProvisionOrTarget(art, hit.case_title)) {
        matchedArticles.push(art);
      }
    }

    // Check for section mentions
    for (const sec of targets.sections) {
      if (matchesProvisionOrTarget(sec, text) || matchesProvisionOrTarget(sec, hit.case_title)) {
        matchedSections.push(sec);
      }
    }

    const matchedTargets = [...matchedArticles, ...matchedSections];

    // If query asked for specific articles/sections, and chunk has NONE of them:
    if (matchedTargets.length === 0) {
      let rejectionReason = `Does not mention or discuss target provisions (${targets.allTargets.join(", ")})`;
      if (detectedProvisions.length > 0) {
        rejectionReason = `Discusses unrelated provisions (${detectedProvisions.slice(0, 3).join(", ")}) instead of target provisions (${targets.allTargets.join(", ")})`;
      } else if (
        lowerText.includes("air conditioner") ||
        lowerText.includes("commission") ||
        lowerText.includes("supply order")
      ) {
        rejectionReason = `Commercial contract dispute regarding supply commission; zero constitutional or target provision relevance`;
      } else if (
        lowerText.includes("prosecutrix") ||
        lowerText.includes("164 crpc") ||
        lowerText.includes("examination-in-chief")
      ) {
        rejectionReason = `Witness deposition record; zero discussion of target provisions`;
      }

      return {
        isRelevant: false,
        relevanceCategory: "IRRELEVANT" as const,
        relevanceReason: rejectionReason,
        targetMatches: [],
        relevantExcerpt: "",
        detectedProvisions,
        page_number,
        paragraph_id,
      };
    }

    // Target matched! Extract the most relevant excerpt sentence/paragraph
    const sentences = text.replace(/\s+/g, " ").split(/(?<=[.!?])\s+/);
    const relevantSentences = sentences.filter((s) =>
      matchedTargets.some((t) => matchesProvisionOrTarget(t, s))
    );

    const relevantExcerpt =
      relevantSentences.slice(0, 3).join(" ") || sentences.slice(0, 2).join(" ");

    let relevanceCategory: "DIRECT_EVIDENCE" | "SUPPORTING_CONTEXT" | "CONTRARY_OR_QUALIFYING" = "DIRECT_EVIDENCE";
    const lowerExcerpt = relevantExcerpt.toLowerCase();
    if (
      lowerExcerpt.includes("however") ||
      lowerExcerpt.includes("distinguished") ||
      lowerExcerpt.includes("cannot modify") ||
      lowerExcerpt.includes("cannot set aside") ||
      lowerExcerpt.includes("overruled") ||
      lowerExcerpt.includes("exception") ||
      lowerExcerpt.includes("subject to") ||
      lowerExcerpt.includes("qualification")
    ) {
      relevanceCategory = "CONTRARY_OR_QUALIFYING";
    } else if (
      lowerExcerpt.includes("held that") ||
      lowerExcerpt.includes("we hold") ||
      lowerExcerpt.includes("operative") ||
      lowerExcerpt.includes("it is clear that") ||
      lowerExcerpt.includes("laid down") ||
      lowerExcerpt.includes("judgment") ||
      lowerExcerpt.includes("question of law")
    ) {
      relevanceCategory = "DIRECT_EVIDENCE";
    } else {
      relevanceCategory = "SUPPORTING_CONTEXT";
    }

    return {
      isRelevant: true,
      relevanceReason: `Substantively discusses target provisions: ${matchedTargets.join(", ")}`,
      relevanceCategory,
      targetMatches: matchedTargets,
      relevantExcerpt,
      detectedProvisions,
      page_number,
      paragraph_id,
    };
  }

  // B. For conceptual / non-statutory queries:
  const matchedConcepts = targets.concepts.filter((c) => fullText.includes(c));
  if (matchedConcepts.length > 0) {
    const sentences = text.replace(/\s+/g, " ").split(/(?<=[.!?])\s+/);
    const relevantSentences = sentences.filter((s) =>
      matchedConcepts.some((c) => s.toLowerCase().includes(c))
    );
    const relevantExcerpt =
      relevantSentences.slice(0, 3).join(" ") || sentences.slice(0, 2).join(" ");

    return {
      isRelevant: true,
      relevanceReason: `Addresses query concepts: ${matchedConcepts.join(", ")}`,
      relevanceCategory: "DIRECT_EVIDENCE" as const,
      targetMatches: matchedConcepts,
      relevantExcerpt,
      detectedProvisions,
      page_number,
      paragraph_id,
    };
  }

  // Fallback: For general queries without explicit target provisions, require genuine topical overlap
  const stopWords = new Set([
    "the", "and", "under", "with", "from", "that", "this", "which", "for", "are",
    "was", "were", "been", "have", "has", "had", "does", "did", "not", "but",
    "any", "all", "each", "into", "over", "such", "than", "then", "there", "their",
    "about", "against", "between", "through", "during", "before", "after", "above",
    "below", "upon", "down", "off", "out", "only", "same", "some", "what", "when",
    "where", "who", "whom", "why", "how", "case", "order", "court", "rules", "rule",
    "anything", "something", "know", "tell", "give", "show", "details"
  ]);
  const uniqueSubstantiveWords = Array.from(
    new Set(
      targets.rawQuery
        ? targets.rawQuery
            .toLowerCase()
            .split(/[^a-z0-9]+/)
            .filter((w) => w.length > 3 && !stopWords.has(w))
        : []
    )
  );

  const matchingSubstantiveWords = uniqueSubstantiveWords.filter((w) =>
    new RegExp(`\\b${w}`, "i").test(fullText)
  );

  const hasSubstantiveOverlap =
    matchingSubstantiveWords.length >= 3 ||
    (uniqueSubstantiveWords.length > 0 &&
      matchingSubstantiveWords.length >= 2 &&
      matchingSubstantiveWords.length / uniqueSubstantiveWords.length >= 0.5);

  const isScoreAcceptable = hit.score > 0.4 || hit.score > 20;

  if (isScoreAcceptable && targets.allTargets.length === 0 && hasSubstantiveOverlap) {
    return {
      isRelevant: true,
      relevanceReason: `Substantive topical overlap on query keywords: ${matchingSubstantiveWords.join(", ")}`,
      relevanceCategory: "SUPPORTING_CONTEXT" as const,
      targetMatches: matchingSubstantiveWords,
      relevantExcerpt: text.slice(0, 300),
      detectedProvisions,
      page_number,
      paragraph_id,
    };
  }

  return {
    isRelevant: false,
    relevanceReason: `No verified topical overlap with query targets`,
    relevanceCategory: "IRRELEVANT" as const,
    targetMatches: [],
    relevantExcerpt: "",
    detectedProvisions,
    page_number,
    paragraph_id,
  };
}
