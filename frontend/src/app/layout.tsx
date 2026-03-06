import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Newsroom Lens — Multilingual News Bias Analysis",
  description: "Detect bias, analyze sentiment, and compare sources across 200+ languages. Powered by local AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body style={{ background: "#0d0d0d", minHeight: "100vh" }}>{children}</body>
    </html>
  );
}
