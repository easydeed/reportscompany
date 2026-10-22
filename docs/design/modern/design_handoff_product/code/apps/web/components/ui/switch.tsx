'use client'

import * as React from 'react'
import * as SwitchPrimitive from '@radix-ui/react-switch'
import { cn } from '@/lib/utils'

// App v3: 40×24, track success-green on / disabled-grey off, 18px white knob.
function Switch({ className, ...props }: React.ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      className={cn(
        'peer relative inline-flex h-6 w-10 shrink-0 cursor-pointer items-center rounded-full border-0 transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring-alpha)] disabled:cursor-not-allowed disabled:opacity-60',
        'data-[state=checked]:bg-[var(--success)] data-[state=unchecked]:bg-[var(--disabled)]',
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className="pointer-events-none block size-[18px] rounded-full bg-white shadow-[0_1px_3px_rgba(0,0,0,0.25)] transition-transform data-[state=checked]:translate-x-[19px] data-[state=unchecked]:translate-x-[3px]"
      />
    </SwitchPrimitive.Root>
  )
}

export { Switch }
