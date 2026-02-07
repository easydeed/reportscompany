"use client"

import { motion } from "framer-motion"
import {
  Search,
  Plus,
  Upload,
  Users,
  Mail,
  Phone,
  MoreHorizontal,
  ArrowUpDown,
  Filter,
  Send,
  UserPlus,
  BarChart3,
} from "lucide-react"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const contacts = [
  { initials: "SJ", name: "Sarah Johnson", email: "sarah.johnson@email.com", phone: "(512) 555-0142", group: "Austin Buyers", type: "Client", lastSent: "Jan 28, 2026", opens: 12, color: "bg-[#6366F1]" },
  { initials: "MC", name: "Michael Chen", email: "m.chen@brokerage.com", phone: "(512) 555-0298", group: "Agent Partners", type: "Agent", lastSent: "Jan 25, 2026", opens: 8, color: "bg-[#4338CA]" },
  { initials: "LP", name: "Lisa Patel", email: "lisa.patel@email.com", phone: "(512) 555-0377", group: "Westlake Sellers", type: "Client", lastSent: "Jan 22, 2026", opens: 15, color: "bg-[#818CF8]" },
  { initials: "DR", name: "David Rodriguez", email: "david.r@realty.com", phone: "(512) 555-0451", group: "Agent Partners", type: "Agent", lastSent: "Jan 20, 2026", opens: 6, color: "bg-[#312E81]" },
  { initials: "AW", name: "Amanda Wilson", email: "amanda.w@email.com", phone: "(512) 555-0533", group: "Austin Buyers", type: "Client", lastSent: "Jan 18, 2026", opens: 9, color: "bg-[#475569]" },
]

const groups = [
  { name: "All Contacts", count: 247 },
  { name: "Austin Buyers", count: 84 },
  { name: "Westlake Sellers", count: 56 },
  { name: "Agent Partners", count: 38 },
  { name: "Downtown Investors", count: 41 },
]

const stats = [
  { label: "Total contacts", value: "247", icon: Users },
  { label: "Reports sent", value: "1,842", icon: Send },
  { label: "Avg open rate", value: "68%", icon: BarChart3 },
  { label: "New this month", value: "23", icon: UserPlus },
]

export function ContactManagement() {
  return (
    <section id="contacts" className="bg-[#F8FAFC] px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.div variants={fadeUp} className="text-center">
          <h2 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
            Your entire audience, organized
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            Manage contacts, create smart groups, track engagement, and deliver
            the right report to the right people &mdash; all from one dashboard.
          </p>
        </motion.div>

        {/* Stat cards */}
        <motion.div
          variants={fadeUp}
          className="mx-auto mt-14 grid max-w-4xl grid-cols-2 gap-4 md:grid-cols-4"
        >
          {stats.map((s) => (
            <div
              key={s.label}
              className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#EEF2FF]">
                <s.icon className="h-5 w-5 text-[#6366F1]" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{s.value}</p>
                <p className="text-xs text-muted-foreground">{s.label}</p>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Dashboard mockup */}
        <motion.div
          variants={fadeUp}
          className="mx-auto mt-10 overflow-hidden rounded-2xl border border-border bg-card shadow-xl"
        >
          <div className="flex flex-col md:flex-row">
            {/* Sidebar */}
            <div className="w-full border-b border-border bg-[#FAFBFC] p-5 md:w-56 md:border-b-0 md:border-r">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Groups
              </p>
              <div className="mt-3 space-y-1">
                {groups.map((g, i) => (
                  <div
                    key={g.name}
                    className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm ${
                      i === 0
                        ? "bg-[#EEF2FF] font-semibold text-[#6366F1]"
                        : "text-muted-foreground hover:bg-muted/50"
                    }`}
                  >
                    <span>{g.name}</span>
                    <span className={`text-xs ${i === 0 ? "text-[#6366F1]" : "text-muted-foreground/60"}`}>
                      {g.count}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-2 rounded-lg border border-dashed border-border px-3 py-2 text-xs text-muted-foreground">
                <Plus className="h-3.5 w-3.5" />
                New group
              </div>
            </div>

            {/* Main content */}
            <div className="flex-1">
              {/* Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2">
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Search 247 contacts...</span>
                  </div>
                  <div className="flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-medium text-muted-foreground">
                    <Filter className="h-3.5 w-3.5" />
                    Filter
                  </div>
                </div>
                <div className="flex gap-2">
                  <div className="flex items-center gap-1.5 rounded-lg border border-border bg-transparent px-3 py-2 text-xs font-medium text-foreground">
                    <Upload className="h-3.5 w-3.5" />
                    Import CSV
                  </div>
                  <div className="flex items-center gap-1.5 rounded-lg bg-[#6366F1] px-3 py-2 text-xs font-medium text-white">
                    <Plus className="h-3.5 w-3.5" />
                    Add Contact
                  </div>
                </div>
              </div>

              {/* Table header */}
              <div className="hidden grid-cols-[1fr_1fr_auto_auto_auto_auto] items-center gap-4 border-b border-border bg-[#FAFBFC] px-6 py-3 text-xs font-medium uppercase tracking-wide text-muted-foreground md:grid">
                <div className="flex items-center gap-1">
                  Name
                  <ArrowUpDown className="h-3 w-3" />
                </div>
                <span>Email</span>
                <span className="w-28">Phone</span>
                <span className="w-28">Group</span>
                <span className="w-20 text-center">Type</span>
                <span className="w-24 text-right">Last sent</span>
              </div>

              {/* Rows */}
              {contacts.map((c) => (
                <div
                  key={c.email}
                  className="group grid grid-cols-1 items-center gap-2 border-b border-border px-6 py-3.5 last:border-b-0 md:grid-cols-[1fr_1fr_auto_auto_auto_auto] md:gap-4"
                >
                  <div className="flex items-center gap-3">
                    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${c.color}`}>
                      {c.initials}
                    </div>
                    <div>
                      <span className="text-sm font-semibold text-foreground">{c.name}</span>
                      <span className="block text-xs text-muted-foreground md:hidden">{c.email}</span>
                    </div>
                  </div>
                  <div className="hidden items-center gap-2 md:flex">
                    <Mail className="h-3.5 w-3.5 text-muted-foreground/50" />
                    <span className="truncate text-sm text-muted-foreground">{c.email}</span>
                  </div>
                  <div className="hidden w-28 items-center gap-2 md:flex">
                    <Phone className="h-3.5 w-3.5 text-muted-foreground/50" />
                    <span className="text-xs text-muted-foreground">{c.phone}</span>
                  </div>
                  <span className="hidden w-28 text-xs text-muted-foreground md:block">{c.group}</span>
                  <span className={`hidden w-20 rounded-full px-2.5 py-0.5 text-center text-xs font-medium md:block ${
                    c.type === "Client" ? "bg-[#EEF2FF] text-[#4338CA]" : "bg-[#F1F5F9] text-[#475569]"
                  }`}>
                    {c.type}
                  </span>
                  <div className="hidden w-24 items-center justify-end gap-2 md:flex">
                    <span className="text-xs text-muted-foreground">{c.lastSent}</span>
                    <button
                      type="button"
                      className="flex h-7 w-7 items-center justify-center rounded-md opacity-0 transition-opacity hover:bg-muted group-hover:opacity-100"
                      aria-label={`More options for ${c.name}`}
                    >
                      <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                    </button>
                  </div>
                </div>
              ))}

              {/* Table footer */}
              <div className="flex items-center justify-between border-t border-border bg-[#FAFBFC] px-6 py-3">
                <p className="text-xs text-muted-foreground">Showing 5 of 247 contacts</p>
                <div className="flex items-center gap-1">
                  <div className="rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground">Previous</div>
                  <div className="rounded-md bg-[#6366F1] px-2.5 py-1 text-xs font-medium text-white">1</div>
                  <div className="rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground">2</div>
                  <div className="rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground">Next</div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Feature highlights */}
        <motion.div variants={fadeUp} className="mt-10">
          <h3 className="text-center text-xl font-bold text-foreground">
            Simple yet powerful
          </h3>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-4">
            {[
              { icon: Users, label: "Smart groups for easy scheduling" },
              { icon: Upload, label: "CSV import for bulk adds" },
              { icon: Mail, label: "One-click delivery to any group" },
              { icon: BarChart3, label: "Open & click tracking per contact" },
            ].map((p) => (
              <div
                key={p.label}
                className="flex items-center gap-2 rounded-full bg-card px-5 py-2.5 text-sm font-medium text-foreground shadow-sm"
              >
                <p.icon className="h-4 w-4 text-[#6366F1]" />
                {p.label}
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </section>
  )
}
