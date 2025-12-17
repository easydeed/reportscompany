import { apiFetch } from "@/lib/api"
import Link from "next/link"
import { notFound } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Building2,
  Users,
  FileText,
  ArrowLeft,
  Mail,
  Globe,
  Calendar,
  UserPlus,
  ExternalLink,
  CheckCircle,
  XCircle,
  FileUp,
  User,
} from "lucide-react"
import { InviteAgentForm } from "./invite-agent-form"
import { AffiliateActions } from "./affiliate-actions"
import { BulkImportForm } from "./bulk-import-form"
import { AgentHeadshotUpload } from "./agent-headshot-upload"

export const dynamic = 'force-dynamic'

interface Agent {
  account_id: string
  name: string
  slug: string
  plan_slug: string
  is_active: boolean
  created_at: string
  email: string
  first_name: string | null
  last_name: string | null
  avatar_url: string | null
  reports_this_month: number
  last_report_at: string | null
}

interface AffiliateDetail {
  account_id: string
  name: string
  slug: string
  account_type: string
  plan_slug: string
  is_active: boolean
  created_at: string
  branding: {
    brand_display_name: string | null
    logo_url: string | null
    primary_color: string | null
    accent_color: string | null
    rep_photo_url: string | null
    contact_line1: string | null
    contact_line2: string | null
    website_url: string | null
  }
  admin_user?: {
    user_id: string
    email: string
    first_name: string | null
    last_name: string | null
    is_active: boolean
    created_at: string
  }
  agents: Agent[]
  agent_count: number
  reports_this_month: number
}

async function getAffiliate(id: string): Promise<AffiliateDetail | null> {
  try {
    const data = await apiFetch(`/v1/admin/affiliates/${id}`)
    return data
  } catch (error) {
    console.error("Failed to fetch affiliate:", error)
    return null
  }
}

export default async function AffiliateDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const affiliate = await getAffiliate(id)

  if (!affiliate) {
    notFound()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin/affiliates">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-4">
            {affiliate.branding.logo_url ? (
              <img
                src={affiliate.branding.logo_url}
                alt={affiliate.name}
                className="h-12 w-12 rounded object-contain bg-muted"
              />
            ) : (
              <div
                className="h-12 w-12 rounded flex items-center justify-center text-white text-lg font-bold"
                style={{ backgroundColor: affiliate.branding.primary_color || '#7C3AED' }}
              >
                {affiliate.name.charAt(0)}
              </div>
            )}
            <div>
              <h1 className="text-3xl font-display font-bold text-foreground">{affiliate.name}</h1>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={affiliate.is_active ? "default" : "secondary"}>
                  {affiliate.is_active ? "Active" : "Inactive"}
                </Badge>
                <Badge variant="outline">{affiliate.plan_slug}</Badge>
              </div>
            </div>
          </div>
        </div>
        <AffiliateActions affiliate={affiliate} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{affiliate.agent_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports/Month</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{affiliate.reports_this_month}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {affiliate.created_at
                ? new Date(affiliate.created_at).toLocaleDateString()
                : '-'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Website</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {affiliate.branding.website_url ? (
              <a
                href={affiliate.branding.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                Visit
                <ExternalLink className="h-3 w-3" />
              </a>
            ) : (
              <span className="text-muted-foreground">Not set</span>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Admin User */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Admin Contact</CardTitle>
            <CardDescription>Primary account administrator</CardDescription>
          </CardHeader>
          <CardContent>
            {affiliate.admin_user ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span>{affiliate.admin_user.email}</span>
                </div>
                {(affiliate.admin_user.first_name || affiliate.admin_user.last_name) && (
                  <div className="text-sm text-muted-foreground">
                    {affiliate.admin_user.first_name} {affiliate.admin_user.last_name}
                  </div>
                )}
                <div className="flex items-center gap-2">
                  {affiliate.admin_user.is_active ? (
                    <Badge variant="outline" className="text-green-600">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Active
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-red-600">
                      <XCircle className="h-3 w-3 mr-1" />
                      Inactive
                    </Badge>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">No admin user found</p>
            )}
          </CardContent>
        </Card>

        {/* Branding */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Branding</CardTitle>
            <CardDescription>White-label configuration</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Display Name</div>
                <div>{affiliate.branding.brand_display_name || affiliate.name}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Colors</div>
                <div className="flex items-center gap-2">
                  {affiliate.branding.primary_color && (
                    <div
                      className="w-6 h-6 rounded border"
                      style={{ backgroundColor: affiliate.branding.primary_color }}
                      title={`Primary: ${affiliate.branding.primary_color}`}
                    />
                  )}
                  {affiliate.branding.accent_color && (
                    <div
                      className="w-6 h-6 rounded border"
                      style={{ backgroundColor: affiliate.branding.accent_color }}
                      title={`Accent: ${affiliate.branding.accent_color}`}
                    />
                  )}
                  {!affiliate.branding.primary_color && !affiliate.branding.accent_color && (
                    <span className="text-muted-foreground">Not set</span>
                  )}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Contact Line 1</div>
                <div>{affiliate.branding.contact_line1 || <span className="text-muted-foreground">Not set</span>}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Contact Line 2</div>
                <div>{affiliate.branding.contact_line2 || <span className="text-muted-foreground">Not set</span>}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Invite Agent Form */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Invite New Agent
          </CardTitle>
          <CardDescription>
            Add a new agent to be sponsored by {affiliate.name}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <InviteAgentForm affiliateId={affiliate.account_id} affiliateName={affiliate.name} />
        </CardContent>
      </Card>

      {/* Bulk Import */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileUp className="h-5 w-5" />
            Bulk Import Agents
          </CardTitle>
          <CardDescription>
            Import multiple agents at once from a CSV file. Great for full-service onboarding.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BulkImportForm affiliateId={affiliate.account_id} affiliateName={affiliate.name} />
        </CardContent>
      </Card>

      {/* Agents Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Users className="h-5 w-5" />
            Sponsored Agents ({affiliate.agent_count})
          </CardTitle>
          <CardDescription>
            Agents using {affiliate.name}&apos;s branding
          </CardDescription>
        </CardHeader>
        <CardContent>
          {affiliate.agents.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No agents yet</h3>
              <p className="text-muted-foreground">
                Use the form above to invite agents to this affiliate
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Reports/Month</TableHead>
                  <TableHead>Last Report</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="w-[50px]">Headshot</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {affiliate.agents.map((agent) => (
                  <TableRow key={agent.account_id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {agent.avatar_url ? (
                          <img
                            src={agent.avatar_url}
                            alt={agent.name}
                            className="h-8 w-8 rounded-full object-cover"
                          />
                        ) : (
                          <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                            <User className="h-4 w-4 text-muted-foreground" />
                          </div>
                        )}
                        <div>
                          <div className="font-medium">{agent.name}</div>
                          {(agent.first_name || agent.last_name) && (
                            <div className="text-sm text-muted-foreground">
                              {agent.first_name} {agent.last_name}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{agent.email}</TableCell>
                    <TableCell>{agent.reports_this_month}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {agent.last_report_at
                        ? new Date(agent.last_report_at).toLocaleDateString()
                        : 'Never'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={agent.is_active ? "default" : "secondary"}>
                        {agent.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {agent.created_at
                        ? new Date(agent.created_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <AgentHeadshotUpload
                        accountId={agent.account_id}
                        agentName={agent.name}
                        currentHeadshot={agent.avatar_url}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
