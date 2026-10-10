import type { Metadata } from "next";
import { Source_Serif_4, Inter, Cinzel } from "next/font/google";
import "./globals.css";

const cinzel = Cinzel({
  variable: "--font-cinzel",
  subsets: ["latin"],
  display: "swap",
  weight: ["500", "600", "700", "800", "900"],
});

const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  display: "swap",
  weight: ["300", "400", "600", "700"],
  style: ["normal", "italic"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Vidhik — Research the law. Trace every authority.",
  description:
    "Indian legal research system grounded in judicial decisions, certified evidence, and authority provenance across Supreme Court, High Courts, and District Courts.",
  keywords: [
    "Indian Law",
    "Legal Research",
    "Judicial Authority",
    "Supreme Court of India",
    "High Court",
    "Limitation Act",
    "Evidence Grounded",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${cinzel.variable} ${sourceSerif.variable} ${inter.variable}`}>
      <body style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        {children}
      </body>
    </html>
  );
}
