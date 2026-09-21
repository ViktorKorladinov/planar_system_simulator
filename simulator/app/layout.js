export const metadata = {
  title: "Planar Simulator",
  description: "Planar transport system simulator.",
};

import '@/styles/globals.css'

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
