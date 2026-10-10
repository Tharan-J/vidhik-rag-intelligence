import { Matter, RecentActivity, UpcomingItem } from "../types/matter";
import extractedMattersData from "./extracted_matters.json";

// Dynamic matters extracted directly from real judicial records via Gemini AI
export const INITIAL_MATTERS: Matter[] = extractedMattersData as unknown as Matter[];

export const INITIAL_RECENT_ACTIVITY: RecentActivity[] = [
  {
    id: "ACT-001",
    matterId: "MAT-2024-001",
    matterTitle: "Delhi Development Authority v. Ajab Singh",
    type: "document_added",
    title: "Appellate paperbook parsed",
    detail: "FAO (COMM) 20/2022 judgment and record indexed via Gemini 3.5 Flash Lite",
    timestamp: "10 mins ago",
  },
  {
    id: "ACT-002",
    matterId: "MAT-2024-002",
    matterTitle: "Govt. of Maharashtra v. Borse Brothers",
    type: "issue_identified",
    title: "Supreme Court holding extracted",
    detail: "Overruling of N.V. International & Section 37 limitation ratio identified",
    timestamp: "1 hour ago",
  },
  {
    id: "ACT-003",
    matterId: "MAT-2024-001",
    matterTitle: "Delhi Development Authority v. Ajab Singh",
    type: "research_saved",
    title: "Authority saved to matter",
    detail: "Consolidated Engg. Enterprises (2008) 7 SCC 169 linked to Section 34(3) issue",
    timestamp: "Yesterday",
  },
  {
    id: "ACT-004",
    matterId: "MAT-2024-003",
    matterTitle: "Niraj Silk Mills v. Commr. of Customs",
    type: "hearing_updated",
    title: "Statutory appeal record added",
    detail: "CUSAA 26/2022 on raw silk valuation listed before DB-II",
    timestamp: "2 days ago",
  },
  {
    id: "ACT-005",
    matterId: "MAT-2024-004",
    matterTitle: "Bhimrao Yerge v. Kavita Yerge",
    type: "note_created",
    title: "Supervisory writ note drafted",
    detail: "Financial affidavit disclosure checklist under Rajnesh v. Neha guidelines",
    timestamp: "3 days ago",
  },
];

export const INITIAL_UPCOMING_ITEMS: UpcomingItem[] = [
  {
    id: "UP-001",
    matterId: "MAT-2024-001",
    matterTitle: "DDA v. Ajab Singh & Co.",
    title: "Section 34(3) Review Application",
    date: "14 Oct 2026",
    type: "submission",
    court: "Delhi High Court",
  },
  {
    id: "UP-002",
    matterId: "MAT-2024-002",
    matterTitle: "Govt. of Maharashtra v. Borse Brothers",
    title: "Compliance Report on Condonation Exception",
    date: "18 Oct 2026",
    type: "deadline",
    court: "Supreme Court of India",
  },
  {
    id: "UP-003",
    matterId: "MAT-2024-003",
    matterTitle: "Niraj Silk Mills v. Customs",
    title: "Valuation Rule 12 Rebuttal Arguments",
    date: "24 Oct 2026",
    type: "hearing",
    court: "Delhi High Court",
  },
  {
    id: "UP-004",
    matterId: "MAT-2024-004",
    matterTitle: "Bhimrao Yerge v. Kavita Yerge",
    title: "Interim Maintenance Quantum Hearing",
    date: "12 Nov 2026",
    type: "hearing",
    court: "Bombay High Court (Aurangabad)",
  },
];
