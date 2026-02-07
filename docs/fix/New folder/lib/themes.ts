export type ThemeKey = "bold" | "classic" | "elegant" | "modern" | "teal"

export interface Theme {
  key: ThemeKey
  label: string
  fonts: { display: string; body: string }
  colors: {
    primary: string
    accent: string
    surface: string
    textOnPrimary: string
    textOnAccent: string
    muted: string
    border: string
    tableStripe: string
    tableStripe2?: string
  }
  radius: string
  radiusSm: string
  radiusLg: string
}

export const themes: Record<ThemeKey, Theme> = {
  bold: {
    key: "bold",
    label: "Bold",
    fonts: { display: "var(--font-oswald)", body: "var(--font-inter)" },
    colors: {
      primary: "#0F1629",
      accent: "#C9A227",
      surface: "#FFFFFF",
      textOnPrimary: "#FFFFFF",
      textOnAccent: "#0F1629",
      muted: "#6B7280",
      border: "#D1D5DB",
      tableStripe: "#F3F4F6",
    },
    radius: "2px",
    radiusSm: "2px",
    radiusLg: "4px",
  },
  classic: {
    key: "classic",
    label: "Classic",
    fonts: { display: "var(--font-playfair)", body: "var(--font-source-sans)" },
    colors: {
      primary: "#1B365D",
      accent: "#8B7355",
      surface: "#FDFBF7",
      textOnPrimary: "#FFFFFF",
      textOnAccent: "#FFFFFF",
      muted: "#6B7280",
      border: "#D4C5A9",
      tableStripe: "#F7F4ED",
    },
    radius: "4px",
    radiusSm: "4px",
    radiusLg: "6px",
  },
  elegant: {
    key: "elegant",
    label: "Elegant",
    fonts: { display: "var(--font-cormorant)", body: "var(--font-montserrat)" },
    colors: {
      primary: "#1A1A1A",
      accent: "#B8977E",
      surface: "#FAF8F5",
      textOnPrimary: "#FFFFFF",
      textOnAccent: "#1A1A1A",
      muted: "#6B7280",
      border: "#E5E0D8",
      tableStripe: "#F5F2ED",
    },
    radius: "0px",
    radiusSm: "0px",
    radiusLg: "0px",
  },
  modern: {
    key: "modern",
    label: "Modern",
    fonts: { display: "var(--font-space-grotesk)", body: "var(--font-dm-sans)" },
    colors: {
      primary: "#FF6B5B",
      accent: "#1A1F36",
      surface: "#F1F5F9",
      textOnPrimary: "#FFFFFF",
      textOnAccent: "#FFFFFF",
      muted: "#64748B",
      border: "#E2E8F0",
      tableStripe: "#F8FAFC",
    },
    radius: "12px",
    radiusSm: "12px",
    radiusLg: "20px",
  },
  teal: {
    key: "teal",
    label: "Teal",
    fonts: { display: "var(--font-montserrat)", body: "var(--font-montserrat)" },
    colors: {
      primary: "#34D1C3",
      accent: "#18235C",
      surface: "#FFFFFF",
      textOnPrimary: "#18235C",
      textOnAccent: "#FFFFFF",
      muted: "#64748B",
      border: "#D1D5DB",
      tableStripe: "#DFF6F3",
      tableStripe2: "#ECEAF7",
    },
    radius: "6px",
    radiusSm: "6px",
    radiusLg: "10px",
  },
}
