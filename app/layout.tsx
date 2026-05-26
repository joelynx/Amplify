import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Nav } from "@/components/nav";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Amplify — The problem-bank commons for university STEM",
    template: "%s · Amplify",
  },
  description:
    "A peer-reviewed open commons of university STEM problems, with mastery-tracked practice for students, Overleaf-grade authoring for professors, and assessment infrastructure for institutions. Built at IIT-AD. Scaling to every IIT, then everywhere.",
  openGraph: {
    title: "Amplify — The problem-bank commons for university STEM",
    description:
      "Peer-reviewed problems. Mastery-tracked practice. Built at IIT-AD.",
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
        <Nav />
        {children}
      </body>
    </html>
  );
}
