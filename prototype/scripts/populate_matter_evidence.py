#!/usr/bin/env python3
"""
Populate matter-specific evidence into frontend/src/lib/data/extracted_matters.json
Each matter gets realistic, case-specific evidence items mapped by Issue and Claim,
with supporting and contradicting stances, source documents, page/para coordinates,
and related judicial authorities.
"""

import json
from pathlib import Path

MATTERS_FILE = Path("/home/tharan/Seeds/vidhik/frontend/src/lib/data/extracted_matters.json")

EVIDENCE_DATA = {
    "MAT-2024-001": [
        {
            "id": "EV-001-01",
            "matterId": "MAT-2024-001",
            "issueId": "ISSUE-001",
            "issueTitle": "Applicability of Section 5 of the Limitation Act",
            "claim": "Section 34(3) proviso provides an inelastic 30-day outer ceiling beyond the 3-month period, expressly excluding Section 5 of the Limitation Act.",
            "stance": "supporting",
            "evidenceExcerpt": "Section 34(3) of the Act of 1996 provides for a limitation period of three months. The proviso permits the Court to entertain an application within a further period of thirty days, but not thereafter. The phrase 'not thereafter' constitutes an express exclusion of Section 5 of the Limitation Act within the meaning of Section 29(2).",
            "sourceDocument": "FAO_COMM_20_2022.pdf",
            "pageNumber": "Page 14",
            "paragraphId": "Para 21",
            "relatedAuthority": {
                "caseTitle": "Union of India v. M/s Popular Construction Co.",
                "court": "Supreme Court of India",
                "year": "2001",
                "citation": "(2001) 8 SCC 470"
            },
            "isPinned": True,
            "notes": [
                "Leading ratio: Popular Construction strictly closes condonation beyond 120 days total."
            ],
            "confidence": "1.00 Grounded"
        },
        {
            "id": "EV-001-02",
            "matterId": "MAT-2024-001",
            "issueId": "ISSUE-001",
            "issueTitle": "Applicability of Section 5 of the Limitation Act",
            "claim": "Procedural delays by statutory authorities should be condoned liberally under inherent powers where substantial public revenue is prejudiced by an illegal award.",
            "stance": "contradicting",
            "evidenceExcerpt": "Counsel for DDA submitted that substantial public revenue is involved and that rigid procedural fetters ought not to defeat meritorious objections against an exorbitant arbitral award tainted by patent illegality.",
            "sourceDocument": "Written_Submissions_DDA_Appellant.pdf",
            "pageNumber": "Page 5",
            "paragraphId": "Para 9",
            "relatedAuthority": {
                "caseTitle": "State of Nagaland v. Lipok AO",
                "court": "Supreme Court of India",
                "year": "2005",
                "citation": "(2005) 3 SCC 752"
            },
            "isPinned": False,
            "notes": [
                "DDA argument rejected by Division Bench in view of Section 29(2) Limitation Act."
            ],
            "confidence": "0.94 Grounded"
        },
        {
            "id": "EV-001-03",
            "matterId": "MAT-2024-001",
            "issueId": "ISSUE-002",
            "issueTitle": "Computation of Limitation from Additional Award",
            "claim": "Limitation under Section 34(3) begins afresh on the date on which the Section 33 request was disposed of and signed copy of the additional award received (03.07.2018).",
            "stance": "supporting",
            "evidenceExcerpt": "Under Section 34(3), if a request had been made under Section 33, the period of three months begins on the date on which that request had been disposed of by the arbitral tribunal. Here, the Additional Award was signed on 30.06.2018 and received on 03.07.2018.",
            "sourceDocument": "FAO_COMM_20_2022.pdf",
            "pageNumber": "Page 9",
            "paragraphId": "Para 14",
            "relatedAuthority": {
                "caseTitle": "M/s Ved Prakash Mithal and Sons v. Union of India",
                "court": "Supreme Court of India",
                "year": "2018",
                "citation": "2018 SCC OnLine SC 3181"
            },
            "isPinned": True,
            "notes": [
                "Bench agreed that limitation period runs from 03.07.2018 (receipt of additional award)."
            ],
            "confidence": "0.99 Grounded"
        },
        {
            "id": "EV-001-04",
            "matterId": "MAT-2024-001",
            "issueId": "ISSUE-002",
            "issueTitle": "Computation of Limitation from Additional Award",
            "claim": "Limitation runs strictly from the original award (12.05.2018) because the Section 33 application was merely an afterthought for clerical rectification.",
            "stance": "contradicting",
            "evidenceExcerpt": "Respondent contended that Section 33 application was merely a subterfuge to gain time; the original award dated 12.05.2018 had conclusively determined all substantial claims and rights of the parties.",
            "sourceDocument": "Reply_Objections_Ajab_Singh.pdf",
            "pageNumber": "Page 11",
            "paragraphId": "Para 16",
            "relatedAuthority": {
                "caseTitle": "State of Arunachal Pradesh v. Damani Construction Co.",
                "court": "Supreme Court of India",
                "year": "2007",
                "citation": "(2007) 10 SCC 742"
            },
            "isPinned": False,
            "notes": [],
            "confidence": "0.91 Grounded"
        },
        {
            "id": "EV-001-05",
            "matterId": "MAT-2024-001",
            "issueId": "ISSUE-003",
            "issueTitle": "Sufficiency of Cause for Administrative Delay",
            "claim": "Internal bureaucratic file movements and inter-departmental delays do not constitute 'sufficient cause' to justify delay condonation under Section 34(3).",
            "stance": "supporting",
            "evidenceExcerpt": "The learned Commercial Court noted that after receipt of the Additional Award on 03.07.2018, the file moved lethargically between the Executive Engineer, Chief Engineer, and Legal Department with no day-to-day explanation. Government bodies cannot claim privileged indulgence.",
            "sourceDocument": "Commercial_Court_Order_OMP_12_2018.pdf",
            "pageNumber": "Page 7",
            "paragraphId": "Para 18",
            "relatedAuthority": {
                "caseTitle": "Postmaster General v. Living Media India Ltd.",
                "court": "Supreme Court of India",
                "year": "2012",
                "citation": "(2012) 3 SCC 563"
            },
            "isPinned": True,
            "notes": [
                "Commercial Court relied on Living Media to dismiss DDA's condonation plea."
            ],
            "confidence": "0.98 Grounded"
        },
        {
            "id": "EV-001-06",
            "matterId": "MAT-2024-001",
            "issueId": "ISSUE-003",
            "issueTitle": "Sufficiency of Cause for Administrative Delay",
            "claim": "Misplacement of brief by panel counsel and bonafide procedural confusion constitutes adequate cause within the 30-day discretionary leeway.",
            "stance": "contradicting",
            "evidenceExcerpt": "Affidavit of Executive Engineer dated 24.10.2018 deposes that case papers were erroneously marked to Sh. AK Sharma instead of the designated standing counsel, causing an unavoidable 17-day hiatus during summer vacation.",
            "sourceDocument": "Application_Condonation_Delay_Affidavit.pdf",
            "pageNumber": "Page 3",
            "paragraphId": "Para 6-8",
            "relatedAuthority": {
                "caseTitle": "Collector, Land Acquisition, Anantnag v. Mst. Katiji",
                "court": "Supreme Court of India",
                "year": "1987",
                "citation": "(1987) 2 SCC 107"
            },
            "isPinned": False,
            "notes": [],
            "confidence": "0.88 Grounded"
        }
    ],
    "MAT-2024-002": [
        {
            "id": "EV-002-01",
            "matterId": "MAT-2024-002",
            "issueId": "ISSUE-001",
            "issueTitle": "Applicability of Section 5 of the Limitation Act to Section 37 Arbitration Appeals",
            "claim": "Section 5 of the Limitation Act applies to appeals filed under Section 37 of the Arbitration Act, whether governed by Article 116 of Limitation Act or Section 13(1A) of Commercial Courts Act.",
            "stance": "supporting",
            "evidenceExcerpt": "Section 5 of the Limitation Act does apply to Section 37 appeals, but given the statutory object of speedy resolution of commercial disputes, delay cannot be condoned merely for the asking. Condonation is an exception, not the rule.",
            "sourceDocument": "Civil_Appeal_995_2021_Judgment.pdf",
            "pageNumber": "Pages 30-31",
            "paragraphId": "Para 45",
            "relatedAuthority": {
                "caseTitle": "Consolidated Engg. Enterprises v. Principal Secy. Irrigation Deptt.",
                "court": "Supreme Court of India",
                "year": "2008",
                "citation": "(2008) 7 SCC 169"
            },
            "isPinned": True,
            "notes": [
                "Supreme Court 3-Judge bench ruling settling Section 37 limitation jurisprudence."
            ],
            "confidence": "1.00 Grounded"
        },
        {
            "id": "EV-002-02",
            "matterId": "MAT-2024-002",
            "issueId": "ISSUE-001",
            "issueTitle": "Applicability of Section 5 of the Limitation Act to Section 37 Arbitration Appeals",
            "claim": "Appeals under Section 37 governed by Section 13(1A) of the Commercial Courts Act are subject to an absolute bar of 60 days with no provision for condonation.",
            "stance": "contradicting",
            "evidenceExcerpt": "Respondent contended that Section 13(1A) Commercial Courts Act provides a special limitation period of 60 days which overrides Section 5 by virtue of the non-obstante clause in Section 21 of the Commercial Courts Act.",
            "sourceDocument": "Respondent_Counter_Affidavit_Borse.pdf",
            "pageNumber": "Page 12",
            "paragraphId": "Para 24",
            "relatedAuthority": {
                "caseTitle": "Union of India v. Popular Construction Co.",
                "court": "Supreme Court of India",
                "year": "2001",
                "citation": "(2001) 8 SCC 470"
            },
            "isPinned": False,
            "notes": [],
            "confidence": "0.92 Grounded"
        },
        {
            "id": "EV-002-03",
            "matterId": "MAT-2024-002",
            "issueId": "ISSUE-002",
            "issueTitle": "Correctness of N.V. International Precedent",
            "claim": "The judgment in N.V. International v. State of Assam incorrectly imported Section 34(3) 30-day grace period into Section 37 and is expressly overruled.",
            "stance": "supporting",
            "evidenceExcerpt": "N.V. International was not correctly decided. The Court could not have judicially legislated and grafted the Section 34(3) 30-day limit onto Section 37 appeals without statutory warrant. It stands overruled.",
            "sourceDocument": "Civil_Appeal_995_2021_Judgment.pdf",
            "pageNumber": "Page 48",
            "paragraphId": "Para 63",
            "relatedAuthority": {
                "caseTitle": "Govt. of Maharashtra v. Borse Brothers Engineers & Contractors Pvt. Ltd.",
                "court": "Supreme Court of India",
                "year": "2021",
                "citation": "2021 INSC 194"
            },
            "isPinned": True,
            "notes": [
                "Overruled 2-Judge bench decision in N.V. International (2020) 2 SCC 109."
            ],
            "confidence": "1.00 Grounded"
        },
        {
            "id": "EV-002-04",
            "matterId": "MAT-2024-002",
            "issueId": "ISSUE-002",
            "issueTitle": "Correctness of N.V. International Precedent",
            "claim": "N.V. International correctly harmonized Section 37 with the legislative policy of swift commercial dispute disposal by capping overall delay to 30 days.",
            "stance": "contradicting",
            "evidenceExcerpt": "The principle laid down in N.V. International that an appeal under Section 37 must be filed within 90 + 30 days is consistent with the speedy dispute resolution mandate of the 1996 Act.",
            "sourceDocument": "High_Court_Impugned_Order_Civil_App_75_2019.pdf",
            "pageNumber": "Page 6",
            "paragraphId": "Para 15",
            "relatedAuthority": {
                "caseTitle": "N.V. International v. State of Assam",
                "court": "Supreme Court of India",
                "year": "2020",
                "citation": "(2020) 2 SCC 109"
            },
            "isPinned": False,
            "notes": [],
            "confidence": "0.90 Grounded"
        }
    ],
    "MAT-2024-003": [
        {
            "id": "EV-003-01",
            "matterId": "MAT-2024-003",
            "issueId": "ISSUE-001",
            "issueTitle": "Maintainability of Customs Appeals",
            "claim": "Substantial question of law arises under Section 130 of the Customs Act regarding the re-determination of transaction value without rejecting declared value under Rule 12.",
            "stance": "supporting",
            "evidenceExcerpt": "Tribunal failed to consider that before discarding declared invoice value under Rule 12 of Customs Valuation Rules 2007, the adjudicating authority must record cogent grounds doubting truth or accuracy.",
            "sourceDocument": "CUSAA_26_2022_Appeal.pdf",
            "pageNumber": "Page 8",
            "paragraphId": "Para 14",
            "relatedAuthority": {
                "caseTitle": "Commissioner of Customs v. Sanjivani Non-Ferrous Metals",
                "court": "Supreme Court of India",
                "year": "2019",
                "citation": "(2019) 2 SCC 378"
            },
            "isPinned": True,
            "notes": [
                "Crucial ground establishing High Court jurisdiction under Section 130."
            ],
            "confidence": "0.97 Grounded"
        },
        {
            "id": "EV-003-02",
            "matterId": "MAT-2024-003",
            "issueId": "ISSUE-001",
            "issueTitle": "Maintainability of Customs Appeals",
            "claim": "Appeals involve pure questions of valuation and rate of duty for which exclusive statutory appellate forum is the Supreme Court under Section 130E.",
            "stance": "contradicting",
            "evidenceExcerpt": "Revenue raised preliminary objection that under Section 130(1), no appeal lies to High Court if order relates to determination of any question having relation to rate of duty or value of goods.",
            "sourceDocument": "Revenue_Preliminary_Objections.pdf",
            "pageNumber": "Page 4",
            "paragraphId": "Para 7",
            "relatedAuthority": {
                "caseTitle": "Navin Chemicals Mfg. & Trading Co. Ltd. v. Collector of Customs",
                "court": "Supreme Court of India",
                "year": "1993",
                "citation": "(1993) 4 SCC 320"
            },
            "isPinned": False,
            "notes": [
                "Preliminary objection regarding High Court jurisdiction."
            ],
            "confidence": "0.95 Grounded"
        },
        {
            "id": "EV-003-03",
            "matterId": "MAT-2024-003",
            "issueId": "ISSUE-002",
            "issueTitle": "Legality of Duty Demands and Penalties",
            "claim": "CRCL Chemical Test Report confirms imported fabric composition is 100% mulberry silk, refuting Revenue's misclassification and suppression allegations.",
            "stance": "supporting",
            "evidenceExcerpt": "Central Revenues Control Laboratory (CRCL) Report No. CRCL/DL/2020/481 certified sample as 100% Mulberry raw silk filament yarn, matching Bill of Entry Declaration No. 5819024 exactly.",
            "sourceDocument": "CRCL_Chemical_Test_Report_481.pdf",
            "pageNumber": "Page 2",
            "paragraphId": "Para 4",
            "relatedAuthority": {
                "caseTitle": "Northern Plastic Ltd. v. Collector of Customs",
                "court": "Supreme Court of India",
                "year": "1998",
                "citation": "(1998) 6 SCC 443"
            },
            "isPinned": True,
            "notes": [
                "Scientific test report conclusively counters differential duty claim."
            ],
            "confidence": "0.99 Grounded"
        },
        {
            "id": "EV-003-04",
            "matterId": "MAT-2024-003",
            "issueId": "ISSUE-002",
            "issueTitle": "Legality of Duty Demands and Penalties",
            "claim": "National Import Database (NIDB) contemporaneous import data demonstrates contemporaneous imports of identical goods at significantly higher unit values.",
            "stance": "contradicting",
            "evidenceExcerpt": "Adjudicating authority compared National Import Database (NIDB) transactions for identical grade silk during identical quarter showing declared values lower by 42% without justifiable commercial variance.",
            "sourceDocument": "Order_In_Original_Patparganj_Customs.pdf",
            "pageNumber": "Page 19",
            "paragraphId": "Para 38",
            "relatedAuthority": {
                "caseTitle": "Eicher Tractors Ltd. v. Commissioner of Customs",
                "court": "Supreme Court of India",
                "year": "2001",
                "citation": "(2001) 1 SCC 315"
            },
            "isPinned": False,
            "notes": [],
            "confidence": "0.93 Grounded"
        }
    ],
    "MAT-2024-004": [
        {
            "id": "EV-004-01",
            "matterId": "MAT-2024-004",
            "issueId": "ISSUE-001",
            "issueTitle": "Merger of Interim Order into Final Judgment",
            "claim": "An interlocutory order for interim maintenance merges into the final judgment and cannot survive once the main petition under Section 125 is dismissed on merits.",
            "stance": "supporting",
            "evidenceExcerpt": "By final judgment dated 16.01.2018, the learned Magistrate dismissed Criminal Misc. Application No. 248/2014 holding that the wife deserted the husband without reasonable cause. Interim order cannot have independent life thereafter.",
            "sourceDocument": "Final_Judgment_CMA_248_2014.pdf",
            "pageNumber": "Page 11",
            "paragraphId": "Para 22",
            "relatedAuthority": {
                "caseTitle": "Kanwar Singh Saini v. High Court of Delhi",
                "court": "Supreme Court of India",
                "year": "2012",
                "citation": "(2012) 4 SCC 307"
            },
            "isPinned": True,
            "notes": [
                "Key legal argument: Execution of interim order after final dismissal is an abuse of process."
            ],
            "confidence": "0.98 Grounded"
        },
        {
            "id": "EV-004-02",
            "matterId": "MAT-2024-004",
            "issueId": "ISSUE-001",
            "issueTitle": "Merger of Interim Order into Final Judgment",
            "claim": "Arrears accrued under an interim maintenance order during pendency represent a vested statutory debt enforceable despite subsequent dismissal.",
            "stance": "contradicting",
            "evidenceExcerpt": "Respondent contended that maintenance rights crystalized during the period between interim order dated 06.07.2017 and final dismissal on 16.01.2018 represent legally enforceable debt under Section 125(3).",
            "sourceDocument": "Execution_Petition_Darkhast_45_2018.pdf",
            "pageNumber": "Page 3",
            "paragraphId": "Para 8",
            "relatedAuthority": {
                "caseTitle": "Sunita Kachwaha v. Anil Kachwaha",
                "court": "Supreme Court of India",
                "year": "2014",
                "citation": "(2014) 16 SCC 715"
            },
            "isPinned": False,
            "notes": [],
            "confidence": "0.91 Grounded"
        },
        {
            "id": "EV-004-03",
            "matterId": "MAT-2024-004",
            "issueId": "ISSUE-002",
            "issueTitle": "Suppression of Income and Employment",
            "claim": "Wife actively suppressed substantial commission income from LIC Agency while claiming inability to maintain herself under Section 125 Cr.P.C.",
            "stance": "supporting",
            "evidenceExcerpt": "Form 16A and bank statement of Bank of Maharashtra (A/c No. 6003291823) demonstrates regular commission payments of Rs. 38,500/month received from Life Insurance Corporation of India.",
            "sourceDocument": "LIC_Agency_Commission_Statement.pdf",
            "pageNumber": "Page 4",
            "paragraphId": "Entries 12-24",
            "relatedAuthority": {
                "caseTitle": "Rajnesh v. Neha",
                "court": "Supreme Court of India",
                "year": "2021",
                "citation": "(2021) 2 SCC 324"
            },
            "isPinned": True,
            "notes": [
                "Violation of full income disclosure affidavit mandated under Rajnesh v. Neha."
            ],
            "confidence": "0.99 Grounded"
        },
        {
            "id": "EV-004-04",
            "matterId": "MAT-2024-004",
            "issueId": "ISSUE-002",
            "issueTitle": "Suppression of Income and Employment",
            "claim": "Commission income is volatile, non-guaranteed and insufficient to cover spiraling medical expenditures of minor child.",
            "stance": "contradicting",
            "evidenceExcerpt": "Rebuttal affidavit states LIC renewal commissions have dwindled to negligible sums and are irregular; petitioner earns over Rs. 95,000/month as Senior Assistant in Zilla Parishad.",
            "sourceDocument": "Reply_Affidavit_Kavita_Yerge.pdf",
            "pageNumber": "Page 6",
            "paragraphId": "Para 14",
            "relatedAuthority": {
                "caseTitle": "Chaturbhuj v. Sita Bai",
                "court": "Supreme Court of India",
                "year": "2008",
                "citation": "(2008) 2 SCC 316"
            },
            "isPinned": False,
            "notes": [],
            "confidence": "0.89 Grounded"
        }
    ]
}

def main():
    with open(MATTERS_FILE, "r", encoding="utf-8") as f:
        matters = json.load(f)

    for matter in matters:
        mid = matter.get("id")
        if mid in EVIDENCE_DATA:
            matter["evidence"] = EVIDENCE_DATA[mid]
            print(f"Added {len(EVIDENCE_DATA[mid])} evidence items to matter {mid}")
        else:
            matter["evidence"] = []

    with open(MATTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(matters, f, indent=2, ensure_ascii=False)

    print("Successfully populated evidence for all matters in extracted_matters.json!")

if __name__ == "__main__":
    main()
