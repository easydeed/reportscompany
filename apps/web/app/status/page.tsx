"use client"

import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { CheckCircle, AlertTriangle, XCircle, Clock, RefreshCw } from "lucide-react"
import { useState, useEffect } from "react"

const services = [
  { name: "Web Application", status: "operational", uptime: "99.99%" },
  { name: "Report Generation", status: "operational", uptime: "99.95%" },
  { name: "PDF Rendering", status: "operational", uptime: "99.97%" },
  { name: "Email Delivery", status: "operational", uptime: "99.98%" },
  { name: "MLS Data Sync", status: "operational", uptime: "99.94%" },
  { name: "API", status: "operational", uptime: "99.99%" },
]

const incidents = [
  {
    date: "December 10, 2025",
    title: "Scheduled Maintenance - Database Upgrade",
    status: "resolved",
    description: "Completed database maintenance with zero downtime. All systems operating normally.",
    duration: "45 minutes",
  },
  {
    date: "November 28, 2025",
    title: "Degraded Performance - Report Generation",
    status: "resolved",
    description: "Some users experienced slower report generation times. Issue was identified and resolved.",
    duration: "23 minutes",
  },
  {
    date: "November 15, 2025",
    title: "Email Delivery Delays",
    status: "resolved",
    description: "Scheduled report emails were delayed by up to 15 minutes. Root cause identified and fixed.",
    duration: "35 minutes",
  },
]

const statusConfig = {
  operational: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-500", label: "Operational" },
  degraded: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-500", label: "Degraded" },
  outage: { icon: XCircle, color: "text-red-500", bg: "bg-red-500", label: "Outage" },
  resolved: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-100", label: "Resolved" },
}

export default function StatusPage() {
  const [lastUpdated, setLastUpdated] = useState<string>("")

  useEffect(() => {
    setLastUpdated(new Date().toLocaleString())
  }, [])

  const allOperational = services.every((s) => s.status === "operational")

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 ${
              allOperational ? "bg-green-100" : "bg-yellow-100"
            }`}
          >
            {allOperational ? (
              <>
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="font-semibold text-green-800">All Systems Operational</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                <span className="font-semibold text-yellow-800">Some Systems Degraded</span>
              </>
            )}
          </div>
          <h1 className="font-display font-semibold text-4xl sm:text-5xl text-slate-900 mb-4">
            System Status
          </h1>
          <p className="text-slate-600 flex items-center justify-center gap-2">
            <Clock className="w-4 h-4" />
            Last updated: {lastUpdated || "Loading..."}
          </p>
        </div>
      </section>

      {/* Current Status */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <h2 className="font-display font-semibold text-xl text-slate-900 mb-6">Current Status</h2>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            {services.map((service, index) => {
              const config = statusConfig[service.status as keyof typeof statusConfig]
              const StatusIcon = config.icon

              return (
                <div
                  key={service.name}
                  className={`flex items-center justify-between p-4 ${
                    index !== services.length - 1 ? "border-b border-slate-100" : ""
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <StatusIcon className={`w-5 h-5 ${config.color}`} />
                    <span className="font-medium text-slate-900">{service.name}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-slate-500">{service.uptime} uptime</span>
                    <span
                      className={`text-sm font-medium ${config.color} bg-opacity-10 px-2 py-1 rounded`}
                    >
                      {config.label}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Uptime Stats */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[800px] mx-auto">
          <h2 className="font-display font-semibold text-xl text-slate-900 mb-6">
            90-Day Uptime History
          </h2>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl font-display font-bold text-slate-900">99.97%</span>
              <span className="text-sm text-slate-500">Average uptime</span>
            </div>

            {/* Uptime bars visualization */}
            <div className="flex gap-[2px] h-8 mb-4">
              {Array.from({ length: 90 }).map((_, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-sm ${
                    Math.random() > 0.02 ? "bg-green-500" : "bg-yellow-500"
                  }`}
                  title={`Day ${90 - i}`}
                />
              ))}
            </div>

            <div className="flex justify-between text-sm text-slate-500">
              <span>90 days ago</span>
              <span>Today</span>
            </div>
          </div>
        </div>
      </section>

      {/* Past Incidents */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <h2 className="font-display font-semibold text-xl text-slate-900 mb-6">Past Incidents</h2>

          <div className="space-y-4">
            {incidents.map((incident) => {
              const config = statusConfig[incident.status as keyof typeof statusConfig]

              return (
                <div
                  key={incident.title}
                  className="bg-white rounded-xl border border-slate-200 p-6"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <span className="text-sm text-slate-500">{incident.date}</span>
                      <h3 className="font-semibold text-slate-900">{incident.title}</h3>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 text-sm font-medium ${config.color} ${config.bg} px-2 py-1 rounded`}
                    >
                      <config.icon className="w-3 h-3" />
                      {config.label}
                    </span>
                  </div>
                  <p className="text-slate-600 text-sm mb-2">{incident.description}</p>
                  <p className="text-slate-500 text-sm">Duration: {incident.duration}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Subscribe */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[600px] mx-auto text-center">
          <h2 className="font-display font-semibold text-2xl text-slate-900 mb-4">
            Get Status Updates
          </h2>
          <p className="text-slate-600 mb-6">
            Subscribe to receive notifications when we have scheduled maintenance or incidents.
          </p>
          <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input
              type="email"
              placeholder="you@example.com"
              className="flex-1 px-4 py-3 rounded-lg border border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all"
            />
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Subscribe
            </button>
          </form>
        </div>
      </section>

      <Footer />
    </div>
  )
}
