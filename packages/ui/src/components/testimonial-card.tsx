"use client"

import { cn } from "../lib/utils"
import { Star } from "lucide-react"
import { motion } from "framer-motion"
import Image from "next/image"

interface TestimonialCardProps {
  quote: string
  author: string
  role: string
  company: string
  avatarUrl?: string
  rating?: number
  className?: string
  index?: number
}

export function TestimonialCard({
  quote,
  author,
  role,
  company,
  avatarUrl,
  rating = 5,
  className,
  index = 0,
}: TestimonialCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      className={cn(
        "glass rounded-xl p-6 border border-border hover:border-primary/30 transition-all duration-200",
        className,
      )}
    >
      <div className="flex gap-1 mb-4">
        {Array.from({ length: rating }).map((_, i) => (
          <Star key={i} className="w-4 h-4 fill-accent text-accent" />
        ))}
      </div>
      <blockquote className="text-sm leading-relaxed text-foreground mb-6 text-pretty">"{quote}"</blockquote>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent overflow-hidden">
          {avatarUrl ? (
            <Image src={avatarUrl || "/placeholder.svg"} alt={author} width={40} height={40} className="object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-white font-display font-semibold">
              {author.charAt(0)}
            </div>
          )}
        </div>
        <div>
          <p className="font-display font-semibold text-sm">{author}</p>
          <p className="text-xs text-muted-foreground">
            {role} at {company}
          </p>
        </div>
      </div>
    </motion.div>
  )
}
