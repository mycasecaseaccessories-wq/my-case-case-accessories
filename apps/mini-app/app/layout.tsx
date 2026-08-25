import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "My Case Store",
  description: "My Case accessories inside Telegram",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
