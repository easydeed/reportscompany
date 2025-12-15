import { ImageResponse } from "next/og"

export const runtime = "edge"

export const size = {
  width: 32,
  height: 32,
}

export const contentType = "image/png"

export default function Icon() {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)",
        borderRadius: "6px",
      }}
    >
      {/* House icon with chart bars */}
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
            borderLeft: "8px solid transparent",
            borderRight: "8px solid transparent",
            borderBottom: "7px solid white",
            marginBottom: "1px",
          }}
        />
        {/* House base with chart bars */}
        <div
          style={{
            width: "16px",
            height: "10px",
            background: "white",
            borderRadius: "1px",
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "center",
            gap: "2px",
            padding: "2px",
          }}
        >
          <div style={{ width: "2px", height: "4px", background: "#F26B2B", borderRadius: "1px" }} />
          <div style={{ width: "2px", height: "7px", background: "#F26B2B", borderRadius: "1px" }} />
          <div style={{ width: "2px", height: "5px", background: "#F26B2B", borderRadius: "1px" }} />
        </div>
      </div>
    </div>,
    {
      ...size,
    },
  )
}
