"use client"

import { cn } from "../lib/utils"
import { FileText } from "lucide-react"
import { motion } from "framer-motion"
import Image from "next/image"

interface ReportThumbnailProps {
  title: string
  date: string
  imageUrl?: string
  className?: string
  index?: number
  onClick?: () => void
}

export function ReportThumbnail({ title, date, imageUrl, className, index = 0, onClick }: ReportThumbnailProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      onClick={onClick}
      className={cn(
        "glass rounded-xl border border-border overflow-hidden hover:border-primary/50 transition-all duration-200 hover:shadow-xl cursor-pointer group",
        className,
      )}
    >
      {/* 8.5x11 aspect ratio */}
      <div className="relative aspect-[8.5/11] bg-secondary/50">
        {imageUrl ? (
          <Image
            src={imageUrl || "/placeholder.svg"}
            alt={title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-200"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <FileText className="w-16 h-16 text-muted-foreground/30" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-ink/80 via-ink/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      </div>
      <div className="p-4">
        <h3 className="font-display font-semibold text-sm mb-1 text-balance line-clamp-2 group-hover:text-primary transition-colors">
          {title}
        </h3>
        <p className="text-xs text-muted-foreground">{date}</p>
      </div>
    </motion.div>
  )
}
