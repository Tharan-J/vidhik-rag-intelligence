import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export interface CloudCaseItem {
  id: string;
  filename: string;
  court: string;
  caseNumberHint: string;
  titleHint: string;
  fileSizeBytes: number;
  preview: string;
  sampleType: string;
}

export async function GET() {
  try {
    const highCourtDir = path.resolve(
      process.cwd(),
      "..",
      "research",
      "rag_readiness_audit",
      "high_court",
      "extracted_text"
    );

    const curatedCases: CloudCaseItem[] = [
      {
        id: "CLOUD-000",
        filename: "523382025_2026-07-02.pdf.txt",
        court: "Supreme Court of India",
        caseNumberHint: "Civil Appeal No. 11950 of 2025 (2026 INSC 668)",
        titleHint: "Pooja Ramesh Singh v. Jammu and Kashmir Bank Ltd. & Anr.",
        fileSizeBytes: 19311,
        preview: "Supreme Court judgment setting aside NCLT and NCLAT orders under Section 7 IBC for relying on fake, AI-hallucinated precedents. Detailed principles on AI integrity in judicial adjudication.",
        sampleType: "Supreme Court / IBC & AI Hallucination Precedent",
      },
      {
        id: "CLOUD-001",
        filename: "DLHC010420472019.pdf.txt",
        court: "High Court of Delhi at New Delhi",
        caseNumberHint: "O.M.P. (COMM) 444/2019",
        titleHint: "M/s Chintels India Limited v. M/s Bhayana Builders Pvt. Ltd.",
        fileSizeBytes: 35858,
        preview: "Commercial Arbitration petition under Section 34 challenging arbitral award. Detailed consideration of Section 34(3) limitation, re-filing delay, and Consolidated Engg. Enterprises ratio.",
        sampleType: "Commercial Arbitration / Delay Condonation",
      },
      {
        id: "CLOUD-002",
        filename: "KAHC010027012022.pdf.txt",
        court: "High Court of Karnataka at Bengaluru",
        caseNumberHint: "Writ Petition No. 8888/2020 (S-RES)",
        titleHint: "Patil Malligemadu Chandrashekhar v. State of Karnataka & Ors.",
        fileSizeBytes: 257440,
        preview: "Service jurisprudence and constitutional petition challenging parity in UGC pay scales, grant-in-aid regulations, and statutory entitlement to pensionary benefits under Karnataka Education Act.",
        sampleType: "Constitutional & Service Law",
      },
      {
        id: "CLOUD-003",
        filename: "HCBM020324872022.pdf.txt",
        court: "High Court of Bombay (Nagpur Bench)",
        caseNumberHint: "Criminal Revision Application No. 214/2022",
        titleHint: "Suresh & Anr. v. State of Maharashtra & Anr.",
        fileSizeBytes: 244970,
        preview: "Criminal revision challenging framing of charges under Section 420, 406, and 120-B IPC. Analysis of prima facie ingredients of dishonest misappropriation and discharge applications.",
        sampleType: "Criminal Revision / Commercial Fraud",
      },
      {
        id: "CLOUD-004",
        filename: "DLHC010271232021.pdf.txt",
        court: "High Court of Delhi at New Delhi",
        caseNumberHint: "CS(COMM) 182/2021",
        titleHint: "Puma SE v. Ashok Kumar & Ors.",
        fileSizeBytes: 352913,
        preview: "Commercial intellectual property infringement suit under Trade Marks Act 1999 and Copyright Act 1957. Ex-parte ad-interim injunction, local commissioner appointment, and punitive damages.",
        sampleType: "Commercial Trademark & IP Infringement",
      },
      {
        id: "CLOUD-005",
        filename: "HCMA010327392013.pdf.txt",
        court: "High Court of Madras",
        caseNumberHint: "C.M.A. No. 1294/2013",
        titleHint: "United India Insurance Co. Ltd. v. Selvi & Ors.",
        fileSizeBytes: 161072,
        preview: "Motor Vehicles Act statutory compensation appeal. Assessment of multiplier method, dependency calculation, and future prospects under National Insurance v. Pranay Sethi.",
        sampleType: "Motor Accident Compensation Appellate",
      },
      {
        id: "CLOUD-006",
        filename: "DLHC010384332022.pdf.txt",
        court: "High Court of Delhi at New Delhi",
        caseNumberHint: "W.P.(C) 4921/2022 & CM APPL. 14682/2022",
        titleHint: "Anand & Anand Partners v. Union of India & Ors.",
        fileSizeBytes: 269175,
        preview: "Challenge to administrative tender procurement guidelines, constitutional arbitrariness under Article 14, and public procurement norms.",
        sampleType: "Writ & Public Procurement",
      },
    ];

    // Check if files actually exist on disk to populate real size
    const availableCases = curatedCases.map((c) => {
      const fullPath = path.join(highCourtDir, c.filename);
      if (fs.existsSync(fullPath)) {
        const stats = fs.statSync(fullPath);
        return {
          ...c,
          fileSizeBytes: stats.size,
        };
      }
      return c;
    });

    return NextResponse.json({
      cases: availableCases,
      total_available: availableCases.length,
      storage_location: "Vidhik Authoritative Judicial Repository",
    });
  } catch (err: any) {
    console.error("Failed to load cloud cases:", err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
