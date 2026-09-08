export const metadata = {
  title: "XPlanar Pharma Simulator",
  description: "Simulator for pharma scheduler. Developed by CIIRC.",
};

import '@/styles/globals.css'

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
