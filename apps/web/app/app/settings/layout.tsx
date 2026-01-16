export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Settings submenu is now in the main sidebar
  // This layout just passes through the content
  return <>{children}</>
}
