'use client'

import { useEffect, useState } from 'react'
import { LeadPageClient } from './lead-page-client'
import { Skeleton } from '@/components/ui/skeleton'

interface LeadPageSettings {
  agent_code: string
  url: string
  qr_code_url: string
  full_name: string
  photo_url: string | null
  company_name: string | null
  phone: string | null
  email: string | null
  license_number: string | null
  headline: string
  subheadline: string
  theme_color: string
  enabled: boolean
  visits: number
}

interface ConsumerLead {
  id: string
  consumer_phone: string
  consumer_email: string | null
  property_address: string
  property_city: string
  property_state: string
  property_zip: string
  status: string
  view_count: number
  agent_contact_clicked: boolean
  agent_contact_type: string | null
  pdf_downloaded: boolean
  created_at: string
  updated_at: string
}

export default function LeadPage() {
  const [settings, setSettings] = useState<LeadPageSettings | null>(null)
  const [leads, setLeads] = useState<ConsumerLead[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [settingsRes, leadsRes] = await Promise.all([
          fetch('/api/proxy/v1/me/lead-page', { credentials: 'include' }),
          fetch('/api/proxy/v1/me/leads', { credentials: 'include' }),
        ])

        if (settingsRes.ok) {
          setSettings(await settingsRes.json())
        }
        if (leadsRes.ok) {
          const data = await leadsRes.json()
          setLeads(data?.leads || [])
        }
      } catch (err) {
        console.error('Failed to load lead page data:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return <LeadPageSkeleton />
  }

  return <LeadPageClient initialSettings={settings} initialLeads={leads} />
}

function LeadPageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-7 w-32 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-9 w-28 rounded-md" />
      </div>
      <div className="bg-card border border-border rounded-xl p-6">
        <Skeleton className="h-5 w-48 mb-4" />
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <Skeleton className="h-4 w-28 mb-2" />
            <Skeleton className="h-12 w-full rounded-lg" />
          </div>
          <div>
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-24 w-24 rounded-xl" />
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-border">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="text-center p-4 rounded-xl bg-muted/30">
              <Skeleton className="h-4 w-4 mx-auto mb-2" />
              <Skeleton className="h-7 w-12 mx-auto mb-1" />
              <Skeleton className="h-3 w-16 mx-auto" />
            </div>
          ))}
        </div>
      </div>
      <div className="bg-card border border-border rounded-xl p-6">
        <Skeleton className="h-5 w-24 mb-4" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 rounded-xl bg-muted/30 mb-3">
            <Skeleton className="h-4 w-60 mb-2" />
            <Skeleton className="h-3 w-40" />
          </div>
        ))}
      </div>
    </div>
  )
}
