import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SSR Market Research",
  description: "Synthetic Market Research using Semantic Similarity Rating",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>
          <div className="min-h-screen bg-background">
            <header className="border-b">
              <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                  <Link href="/" className="text-xl font-bold">
                    SSR Market Research
                  </Link>
                  <nav className="flex gap-4">
                    <Link
                      href="/surveys/new"
                      className="text-sm text-muted-foreground hover:text-foreground"
                    >
                      Single Survey
                    </Link>
                    <Link
                      href="/surveys/compare"
                      className="text-sm text-muted-foreground hover:text-foreground"
                    >
                      A/B Testing
                    </Link>
                  </nav>
                </div>
              </div>
            </header>
            <main className="container mx-auto px-4 py-8">{children}</main>
          </div>
        </Providers>
        <Toaster />
      </body>
    </html>
  );
}
