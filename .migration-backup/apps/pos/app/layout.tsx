import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "My Case POS",
  description: "My Case online-first POS foundation",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
