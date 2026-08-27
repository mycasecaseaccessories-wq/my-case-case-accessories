import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "My Case Admin",
  description: "My Case admin foundation",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
