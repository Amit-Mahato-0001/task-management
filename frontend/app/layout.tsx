import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Task Manager",
  description: "Simple task management app with Google sign-in",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
