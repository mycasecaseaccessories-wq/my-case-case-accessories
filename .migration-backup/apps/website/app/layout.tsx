import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "My Case v1",
  description: "My Case customer website foundation",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
