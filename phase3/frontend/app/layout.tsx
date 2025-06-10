import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: 'swap',
});

export const metadata: Metadata = {
  title: "🔥 Reddit Pain Finder | AI-Powered Market Research",
  description: "Discover and analyze pain points across Reddit communities to identify business opportunities. Advanced AI-powered dashboard for market research and trend analysis.",
  keywords: ["reddit analysis", "market research", "AI dashboard", "pain points", "business opportunities"],
  authors: [{ name: "Reddit Pain Finder Team" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: "#3b82f6",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} antialiased min-h-screen`}
        style={{
          background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a3e 25%, #2d1b69 50%, #0f0f23 100%)',
          backgroundAttachment: 'fixed'
        }}
      >
        <div className="relative">
          {/* Background decoration */}
          <div className="fixed inset-0 overflow-hidden pointer-events-none">
            <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl"></div>
            <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl"></div>
          </div>
          
          {/* Grid pattern overlay */}
          <div className="fixed inset-0 opacity-20 pointer-events-none">
            <div className="absolute inset-0" style={{
              backgroundImage: `
                linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px'
            }}></div>
          </div>
          
          <div className="relative z-10">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
