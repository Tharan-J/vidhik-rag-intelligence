import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const docQuery = searchParams.get("doc") || "2021 INSC 194";

    let data: any = null;
    try {
      const res = await fetch(`http://127.0.0.1:8008/doc?id=${encodeURIComponent(docQuery)}&max=20`, {
        signal: AbortSignal.timeout(3000),
      });
      if (res.ok) {
        data = await res.json();
      }
    } catch {}

    if (!data) {
      const prototypeDir = path.resolve(process.cwd(), "..", "prototype");
      const scriptPath = path.join(prototypeDir, "scripts", "retrieval_bridge.py");
      const cmd = `python3 "${scriptPath}" --doc "${docQuery}"`;
      const { stdout } = await execAsync(cmd, { cwd: prototypeDir, timeout: 20000 });
      data = JSON.parse(stdout);
    }

    return NextResponse.json({
      success: true,
      caseName: "Government of Maharashtra v. M/s Borse Brothers Engineers & Contractors Pvt. Ltd.",
      citation: "2021 INSC 194 | [2021] 3 S.C.R. 193",
      court: "Supreme Court of India",
      bench: "Justice R.F. Nariman, Justice B.R. Gavai, Justice Hrishikesh Roy",
      dateOfJudgment: "19 March 2021",
      pdfSourcePath: "research/legal_data/supreme_court/pdfs_stage1_candidates/year=2021/2021_3_193_254_EN.pdf",
      pageSize: 62,
      fileSize: "830 KB",
      keyIssues: [
        "Limitation period for filing appeal under Section 37 of Arbitration and Conciliation Act, 1996",
        "Applicability of Section 5 of Limitation Act, 1963 to Section 13(1A) of Commercial Courts Act, 2015",
        "Threshold of 'sufficient cause' for condoning delay in commercial appeals",
      ],
      ratioDecidendi:
        "The Supreme Court held that Section 5 of the Limitation Act applies to appeals under Section 37 of the Arbitration Act, but delay beyond the statutory period (60/90 days) can be condoned only by way of exception and not as a rule. 'Sufficient cause' is not elastic enough to permit routine bureaucratic or lethargic delays in commercial matters.",
      ...data,
    });
  } catch (err: any) {
    return NextResponse.json(
      {
        success: false,
        error: err.message || "Failed to retrieve document demonstration",
      },
      { status: 500 }
    );
  }
}
