import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center justify-center rounded-full border px-[9px] py-[3px] text-[12px] font-semibold w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-[var(--ring)] focus-visible:ring-[var(--ring-alpha)] focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow] overflow-hidden',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90',
        destructive:
          'border-transparent bg-destructive text-white [a&]:hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60',
        outline:
          'text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground',

        // ── Design's semantic status pairs, fixed (tokens.css) ───────────
        // The ONLY tinted fills permitted on chrome. Not derived from brand or
        // theme — a status is a fact about a thing, not a decoration, so the
        // colour cannot move with an account's palette. `clicked` is the one
        // that reads the agent's accent, because a click is the agent's event.
        opened:
          'border-transparent bg-[var(--success-muted)] text-[var(--success-foreground)]',
        done:
          'border-transparent bg-[var(--success-muted)] text-[var(--success-foreground)]',
        called:
          'border-transparent bg-[var(--success-muted)] text-[var(--success-foreground)]',
        sent:
          'border-transparent bg-[var(--neutral-muted)] text-muted-foreground',
        bounced:
          'border-transparent bg-[var(--destructive-muted)] text-[var(--destructive-foreground)]',
        failed:
          'border-transparent bg-[var(--destructive-muted)] text-[var(--destructive-foreground)]',
        running:
          'border-transparent bg-[var(--info-muted)] text-[var(--info-foreground)]',
        hot:
          'border-transparent bg-[var(--warning-muted)] text-[var(--warning-foreground)]',
        new:
          'border-transparent bg-primary text-primary-foreground',
        lead:
          'border-transparent bg-primary text-primary-foreground',
        clicked:
          'border-transparent bg-accent text-accent-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

function Badge({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentPropsWithoutRef<'span'> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : 'span'

  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }

