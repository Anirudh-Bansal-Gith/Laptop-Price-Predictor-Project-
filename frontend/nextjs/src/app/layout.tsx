import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Laptop Price Predictor | Market Valuation Service",
  description: "Machine learning platform estimating laptop market prices from technical hardware specifications.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
