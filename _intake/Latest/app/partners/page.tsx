"use client"

import type React from "react"

import { motion } from "framer-motion"
import {
  Building2,
  FileText,
  CreditCard,
  Shield,
  ArrowRight,
  Users,
  TrendingUp,
  Clock,
  CheckCircle2,
} from "lucide-react"
import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { SectionWrapper } from "@/components/section-wrapper"
import { FeatureGrid } from "@/components/feature-grid"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { useState } from "react"
import { useToast } from "@/hooks/use-toast"

const features = [
  {
    icon: Building2,
    title: "Sponsorships",
    description: "Your brand on every report your agents generate. Build awareness and strengthen relationships.",
  },
  {
    icon: FileText,
    title: "Co-branded PDFs",
    description: "Seamlessly integrate your logo, colors, and contact info into professional market reports.",
  },
  {
    icon: CreditCard,
    title: "Credits & Ledger",
    description: "Simple credit-based billing. Track usage, set limits, and manage costs with full transparency.",
  },
  {
    icon: Shield,
    title: "Admin Console",
    description: "Centralized dashboard to manage agents, monitor usage, and control branding across your network.",
  },
]

const flowSteps = [
  { title: "Bulk invite", description: "Add your agents in seconds" },
  { title: "Auto-brand", description: "Your logo on every report" },
  { title: "Scheduled reports", description: "Automated delivery" },
  { title: "Monthly invoice", description: "Simple, predictable billing" },
]

const kpis = [
  { value: "500+", label: "Title Companies" },
  { value: "15K+", label: "Active Agents" },
  { value: "2M+", label: "Reports Generated" },
  { value: "99.9%", label: "Uptime SLA" },
]

export default function PartnersPage() {
  const [formData, setFormData] = useState({
    company: "",
    name: "",
    email: "",
    phone: "",
    message: "",
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500))

    toast({
      title: "Application received!",
      description: "Our partnerships team will contact you within 24 hours.",
    })

    setFormData({ company: "", name: "", email: "", phone: "", message: "" })
    setIsSubmitting(false)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero */}
      <SectionWrapper className="pt-32 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="max-w-4xl mx-auto text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6 border border-primary/20">
            <Building2 className="w-4 h-4" />
            Title Partner Program
          </div>
          <h1 className="font-display text-5xl md:text-6xl font-bold text-balance mb-6">
            Power Your Network with Premium Market Reports
          </h1>
          <p className="text-xl text-muted-foreground text-balance mb-8 leading-relaxed">
            Join leading title companies providing their agents with instant access to beautiful, data-driven market
            reports—fully branded with your company identity.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Button size="lg" className="gap-2 bg-gradient-to-r from-primary to-accent hover:opacity-90">
              Become a Partner <ArrowRight className="w-4 h-4" />
            </Button>
            <Button size="lg" variant="outline" className="border-border/50 bg-transparent">
              Schedule Demo
            </Button>
          </div>
        </motion.div>
      </SectionWrapper>

      {/* Features Grid */}
      <SectionWrapper className="py-20 bg-muted/20">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
            Everything You Need to Empower Your Agents
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-balance">
            A complete platform designed specifically for title companies and their agent networks.
          </p>
        </div>
        <FeatureGrid features={features} columns={2} />
      </SectionWrapper>

      {/* Flow Card */}
      <SectionWrapper className="py-20">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">Simple Setup, Powerful Results</h2>
            <p className="text-lg text-muted-foreground text-balance">
              Get your entire network up and running in minutes, not weeks.
            </p>
          </div>

          <Card className="p-8 md:p-12 bg-gradient-to-br from-background to-muted/20 border-2 border-border/50 hover:shadow-xl transition-shadow">
            <div className="grid md:grid-cols-4 gap-8">
              {flowSteps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.2, delay: index * 0.1 }}
                  className="relative"
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mb-4">
                      <span className="font-display text-xl font-bold text-primary">{index + 1}</span>
                    </div>
                    <h3 className="font-display text-lg font-semibold mb-2">{step.title}</h3>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                  </div>

                  {index < flowSteps.length - 1 && (
                    <div className="hidden md:block absolute top-6 left-[calc(50%+24px)] w-[calc(100%-48px)]">
                      <ArrowRight className="w-5 h-5 text-primary/50 mx-auto" />
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </Card>
        </div>
      </SectionWrapper>

      {/* KPI Strip */}
      <SectionWrapper className="py-16 bg-gradient-to-br from-primary to-accent text-white">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {kpis.map((kpi, index) => (
            <motion.div
              key={kpi.label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
              className="text-center"
            >
              <div className="font-display text-4xl md:text-5xl font-bold text-white mb-2">{kpi.value}</div>
              <div className="text-sm text-white/80">{kpi.label}</div>
            </motion.div>
          ))}
        </div>
      </SectionWrapper>

      {/* Benefits Section */}
      <SectionWrapper className="py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2 }}
          >
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-6">Why Title Companies Choose Us</h2>
            <div className="space-y-4">
              {[
                "Strengthen agent relationships with valuable tools",
                "Increase brand visibility on every report",
                "Simple credit-based billing with full transparency",
                "White-glove onboarding and dedicated support",
                "Enterprise-grade security and compliance",
                "Detailed usage analytics and reporting",
              ].map((benefit, index) => (
                <motion.div
                  key={benefit}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.15, delay: index * 0.05 }}
                  className="flex items-start gap-3"
                >
                  <CheckCircle2 className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                  <span className="text-lg">{benefit}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2 }}
          >
            <Card className="p-8 bg-gradient-to-br from-primary/5 to-accent/5 border-2 border-border/50 hover:shadow-xl transition-shadow">
              <div className="space-y-6">
                <div>
                  <Users className="w-12 h-12 text-primary mb-4" />
                  <h3 className="font-display text-2xl font-bold mb-2">Dedicated Partnership Team</h3>
                  <p className="text-muted-foreground">
                    Work directly with our partnerships team to customize the platform for your specific needs and
                    ensure smooth rollout across your network.
                  </p>
                </div>
                <div className="pt-6 border-t">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>24/7 Support</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      <span>Quarterly Reviews</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
      </SectionWrapper>

      {/* CTA Form */}
      <SectionWrapper className="py-20 bg-muted/20">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2 }}
            className="text-center mb-12"
          >
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">Become a Partner</h2>
            <p className="text-lg text-muted-foreground text-balance">
              Join the leading title companies empowering their agents with premium market intelligence.
            </p>
          </motion.div>

          <Card className="p-8 md:p-12 border-border/50 bg-card hover:shadow-xl transition-shadow">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="company">Company Name *</Label>
                  <Input
                    id="company"
                    name="company"
                    value={formData.company}
                    onChange={handleChange}
                    placeholder="Acme Title Company"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Your Name *</Label>
                  <Input
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="John Smith"
                    required
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="john@acmetitle.com"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="(555) 123-4567"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Tell us about your needs</Label>
                <Textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Number of agents, current tools, specific requirements..."
                  rows={4}
                />
              </div>

              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <Button
                  type="submit"
                  size="lg"
                  className="flex-1 gap-2 bg-gradient-to-r from-primary to-accent hover:opacity-90"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Submitting..." : "Submit Application"}
                  {!isSubmitting && <ArrowRight className="w-4 h-4" />}
                </Button>
                <Button type="button" size="lg" variant="outline" className="flex-1 border-border/50 bg-transparent">
                  Schedule a Demo
                </Button>
              </div>

              <p className="text-sm text-muted-foreground text-center">
                Our partnerships team typically responds within 24 hours.
              </p>
            </form>
          </Card>
        </div>
      </SectionWrapper>

      <Footer />
    </div>
  )
}
