import { ImageResponse } from "next/og"

export const runtime = "edge"

export const size = {
  width: 180,
  height: 180,
}

export const contentType = "image/png"

export default function AppleIcon() {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)",
        borderRadius: "40px",
      }}
    >
      {/* House icon with chart bars - scaled up */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* House roof */}
        <div
          style={{
            width: 0,
            height: 0,
            borderLeft: "45px solid transparent",
            borderRight: "45px solid transparent",
            borderBottom: "38px solid white",
            marginBottom: "4px",
          }}
        />
        {/* House base with chart bars */}
        <div
          style={{
            width: "90px",
            height: "54px",
            background: "white",
            borderRadius: "6px",
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "center",
            gap: "10px",
            padding: "10px",
          }}
        >
          <div style={{ width: "12px", height: "22px", background: "#F26B2B", borderRadius: "4px" }} />
          <div style={{ width: "12px", height: "38px", background: "#F26B2B", borderRadius: "4px" }} />
          <div style={{ width: "12px", height: "28px", background: "#F26B2B", borderRadius: "4px" }} />
        </div>
      </div>
    </div>,
    {
      ...size,
    },
  )
}
