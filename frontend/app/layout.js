import "./globals.css";
export const metadata = { title: "DSWOPS", description: "Document Scanner & Work Order Processing System" };
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}