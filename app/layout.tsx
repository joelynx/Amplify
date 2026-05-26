import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Nav } from "@/components/nav";
import { TopProgressBar } from "@/components/top-progress";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Amplify — STEM practice for IIT-AD",
    template: "%s · Amplify",
  },
  description:
    "A bank of university math, physics, and CS problems built by IIT-AD's TAs. Mastery-tracked practice for students. One-click contribution for TAs. Built by Karth and Joel.",
  openGraph: {
    title: "Amplify — STEM practice for IIT-AD",
    description:
      "Mastery-tracked practice. TA-authored questions. Built at IIT-AD.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-white font-sans text-ink-900 antialiased">
        <TopProgressBar />
        <Nav />
        {children}
      </body>
    </html>
  );
}
