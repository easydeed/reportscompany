"use client"

import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { SectionWrapper } from "@/components/section-wrapper"
import { FeatureGrid, FeatureCard } from "@/components/feature-grid"
import { Stepper } from "@/components/stepper"
import { ReportThumbnail } from "@/components/report-thumbnail"
import { TestimonialCard } from "@/components/testimonial-card"
import { CodeTabs } from "@/components/code-tabs"
import { Button } from "@/components/ui/button"
import { useToast } from "@/hooks/use-toast"
import {
  FileText,
  Palette,
  Download,
  Users,
  DollarSign,
  BarChart3,
  Shield,
  CheckCircle2,
  MapPin,
  FileCheck,
  Mail,
  Link2,
  Sparkles,
  Zap,
  Share2,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"

export default function Home() {
  const { toast } = useToast()
  const [currentReportIndex, setCurrentReportIndex] = useState(0)
  const [selectedSample, setSelectedSample] = useState<string | null>(null)

  const reportTypes = [
    { title: "Market Analysis", image: "/real-estate-market-report.png" },
    { title: "Neighborhood Comparison", image: "/neighborhood-comparison-chart.jpg" },
    { title: "Price Trends", image: "/luxury-real-estate-data.jpg" },
    { title: "Investment Analysis", image: "/investment-property-metrics.jpg" },
    { title: "Buyer's Report", image: "/real-estate-market-report.png" },
    { title: "Seller's Report", image: "/neighborhood-comparison-chart.jpg" },
    { title: "CMA Report", image: "/luxury-real-estate-data.jpg" },
    { title: "Area Statistics", image: "/investment-property-metrics.jpg" },
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentReportIndex((prev) => (prev + 1) % reportTypes.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [reportTypes.length])

  const sampleReports = [
    {
      id: "market-analysis",
      title: "Market Analysis Report",
      date: "Q4 2024",
      image: "/real-estate-market-report.png",
    },
    {
      id: "neighborhood",
      title: "Neighborhood Comparison",
      date: "Q4 2024",
      image: "/neighborhood-comparison-chart.jpg",
    },
    { id: "luxury", title: "Luxury Market Trends", date: "Q4 2024", image: "/luxury-real-estate-data.jpg" },
    {
      id: "investment",
      title: "Investment Property Analysis",
      date: "Q4 2024",
      image: "/investment-property-metrics.jpg",
    },
    { id: "cma", title: "Comparative Market Analysis", date: "Q4 2024", image: "/real-estate-market-report.png" },
    { id: "buyer", title: "Buyer's Market Report", date: "Q4 2024", image: "/neighborhood-comparison-chart.jpg" },
    { id: "seller", title: "Seller's Market Report", date: "Q4 2024", image: "/luxury-real-estate-data.jpg" },
    { id: "area", title: "Area Statistics Report", date: "Q4 2024", image: "/investment-property-metrics.jpg" },
  ]

  const pythonCode = `import requests

# Create a new report
response = requests.post(
    "https://api.realtyinsight.com/v1/reports",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "location": "San Francisco, CA",
        "report_type": "market_analysis",
        "format": "pdf"
    }
)

report = response.json()
print(f"Report ID: {report['id']}")
print(f"Status: {report['status']}")`

  const javascriptCode = `// Create a new report
const response = await fetch(
  'https://api.realtyinsight.com/v1/reports',
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      location: 'San Francisco, CA',
      report_type: 'market_analysis',
      format: 'pdf'
    })
  }
);

const report = await response.json();
console.log('Report ID:', report.id);
console.log('Status:', report.status);`

  const pythonCodeGet = `import requests

# Get report details
response = requests.get(
    "https://api.realtyinsight.com/v1/reports/rpt_abc123",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

report = response.json()
print(f"Download URL: {report['download_url']}")
print(f"Created: {report['created_at']}")`

  const javascriptCodeGet = `// Get report details
const response = await fetch(
  'https://api.realtyinsight.com/v1/reports/rpt_abc123',
  {
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY'
    }
  }
);

const report = await response.json();
console.log('Download URL:', report.download_url);
console.log('Created:', report.created_at);`

  const steps = [
    {
      title: "Choose area",
      description: "Select your target market area or neighborhood",
    },
    {
      title: "Pick report type",
      description: "Choose from 8 professional report templates",
    },
    {
      title: "Brand once",
      description: "Add your logo, colors, and contact info",
    },
    {
      title: "Share",
      description: "Download PDF, email, or share via link",
    },
  ]

  return (
    <div className="min-h-screen">
      <Navbar />

      <SectionWrapper className="pt-32 pb-20 relative overflow-hidden" background="gradient">
        {/* Tech background pattern */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none">
          <img src="/abstract-technology-grid-pattern-circuit-board-gra.jpg" alt="" className="w-full h-full object-cover grayscale" />
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-center relative z-10">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
            <h1 className="font-display font-bold text-5xl sm:text-6xl lg:text-7xl mb-6 text-balance">
              MLS data. Beautiful reports. Zero effort.
            </h1>
            <p className="text-xl text-muted-foreground mb-8 text-pretty leading-relaxed">
              Turn live housing data into stunning branded market reports in seconds.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className="bg-primary hover:bg-primary/90 text-lg px-8">
                Start Free Trial
              </Button>
              <Button size="lg" variant="outline" className="text-lg px-8 bg-transparent">
                View Sample Reports
              </Button>
            </div>
          </motion.div>

          <div className="relative h-[600px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentReportIndex}
                initial={{ opacity: 0, scale: 0.95, rotateY: -10 }}
                animate={{ opacity: 1, scale: 1, rotateY: 0 }}
                exit={{ opacity: 0, scale: 0.95, rotateY: 10 }}
                transition={{ duration: 0.25 }}
                className="absolute inset-0"
              >
                <div className="glass rounded-xl border border-border p-4 h-full shadow-2xl">
                  <div className="aspect-[8.5/11] bg-background rounded-lg overflow-hidden border border-border">
                    <img
                      src={reportTypes[currentReportIndex].image || "/placeholder.svg"}
                      alt={reportTypes[currentReportIndex].title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <p className="text-center mt-3 font-display font-semibold text-sm">
                    {reportTypes[currentReportIndex].title}
                  </p>
                </div>
              </motion.div>
            </AnimatePresence>
            <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
              {reportTypes.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentReportIndex(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentReportIndex ? "bg-primary w-8" : "bg-muted-foreground/30"
                  }`}
                  aria-label={`View report ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </div>
      </SectionWrapper>

      <SectionWrapper background="muted">
        <div className="grid md:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0 }}
            className="glass rounded-xl border border-border p-8 text-center"
          >
            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <BarChart3 className="w-7 h-7 text-primary" />
            </div>
            <h3 className="font-display font-bold text-2xl mb-3">Accurate MLS data</h3>
            <p className="text-muted-foreground leading-relaxed">
              Real-time integration with MLS feeds nationwide for the most current market information
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.05 }}
            className="glass rounded-xl border border-border p-8 text-center"
          >
            <div className="w-14 h-14 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-4">
              <Palette className="w-7 h-7 text-accent" />
            </div>
            <h3 className="font-display font-bold text-2xl mb-3">Branded for you</h3>
            <p className="text-muted-foreground leading-relaxed">
              Add your logo, colors, and contact info once. Every report reflects your professional brand
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.1 }}
            className="glass rounded-xl border border-border p-8 text-center"
          >
            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Download className="w-7 h-7 text-primary" />
            </div>
            <h3 className="font-display font-bold text-2xl mb-3">Print-perfect PDFs</h3>
            <p className="text-muted-foreground leading-relaxed">
              High-resolution exports optimized for digital sharing or professional printing
            </p>
          </motion.div>
        </div>
      </SectionWrapper>

      <SectionWrapper>
        <div className="text-center mb-16">
          <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-balance">How It Works</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            From data to delivery in four simple steps
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Step 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0 }}
              className="relative"
            >
              <div className="glass rounded-xl border border-border p-6 h-full">
                <div className="aspect-square rounded-lg bg-primary/5 mb-4 overflow-hidden relative">
                  <img src="/map-location-pin-real-estate-neighborhood-illustra.jpg" alt="Choose area" className="w-full h-full object-cover" />
                  <div className="absolute top-3 left-3 w-10 h-10 rounded-full bg-primary flex items-center justify-center font-display font-bold text-white">
                    1
                  </div>
                </div>
                <h3 className="font-display font-bold text-xl mb-2">Choose area</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Select your target market area or neighborhood with our intuitive map interface
                </p>
              </div>
              {/* Connector line */}
              <div className="hidden lg:block absolute top-1/3 -right-4 w-8 h-0.5 bg-gradient-to-r from-primary/50 to-transparent" />
            </motion.div>

            {/* Step 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.1 }}
              className="relative"
            >
              <div className="glass rounded-xl border border-border p-6 h-full">
                <div className="aspect-square rounded-lg bg-accent/5 mb-4 overflow-hidden relative">
                  <img src="/document-templates-report-types-grid-layout-illust.jpg" alt="Pick report type" className="w-full h-full object-cover" />
                  <div className="absolute top-3 left-3 w-10 h-10 rounded-full bg-accent flex items-center justify-center font-display font-bold text-white">
                    2
                  </div>
                </div>
                <h3 className="font-display font-bold text-xl mb-2">Pick report type</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Choose from 8 professional report templates designed for every scenario
                </p>
              </div>
              <div className="hidden lg:block absolute top-1/3 -right-4 w-8 h-0.5 bg-gradient-to-r from-accent/50 to-transparent" />
            </motion.div>

            {/* Step 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.2 }}
              className="relative"
            >
              <div className="glass rounded-xl border border-border p-6 h-full">
                <div className="aspect-square rounded-lg bg-primary/5 mb-4 overflow-hidden relative">
                  <img src="/branding-logo-colors-customization-palette-illustr.jpg" alt="Brand once" className="w-full h-full object-cover" />
                  <div className="absolute top-3 left-3 w-10 h-10 rounded-full bg-primary flex items-center justify-center font-display font-bold text-white">
                    3
                  </div>
                </div>
                <h3 className="font-display font-bold text-xl mb-2">Brand once</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Add your logo, colors, and contact info. Set it once, use it forever
                </p>
              </div>
              <div className="hidden lg:block absolute top-1/3 -right-4 w-8 h-0.5 bg-gradient-to-r from-primary/50 to-transparent" />
            </motion.div>

            {/* Step 4 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.3 }}
              className="relative"
            >
              <div className="glass rounded-xl border border-border p-6 h-full">
                <div className="aspect-square rounded-lg bg-accent/5 mb-4 overflow-hidden relative">
                  <img src="/share-send-email-link-pdf-download-illustration.jpg" alt="Share" className="w-full h-full object-cover" />
                  <div className="absolute top-3 left-3 w-10 h-10 rounded-full bg-accent flex items-center justify-center font-display font-bold text-white">
                    4
                  </div>
                </div>
                <h3 className="font-display font-bold text-xl mb-2">Share</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Download PDF, email directly, or share via secure link instantly
                </p>
              </div>
            </motion.div>
          </div>

          {/* Feature highlights below */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.4 }}
            className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            <div className="glass rounded-lg border border-border p-4 text-center">
              <Zap className="w-6 h-6 text-primary mx-auto mb-2" />
              <p className="text-sm font-medium">30 seconds</p>
              <p className="text-xs text-muted-foreground">Average generation time</p>
            </div>
            <div className="glass rounded-lg border border-border p-4 text-center">
              <Sparkles className="w-6 h-6 text-accent mx-auto mb-2" />
              <p className="text-sm font-medium">8 templates</p>
              <p className="text-xs text-muted-foreground">Professional designs</p>
            </div>
            <div className="glass rounded-lg border border-border p-4 text-center">
              <Palette className="w-6 h-6 text-primary mx-auto mb-2" />
              <p className="text-sm font-medium">Full branding</p>
              <p className="text-xs text-muted-foreground">Your logo & colors</p>
            </div>
            <div className="glass rounded-lg border border-border p-4 text-center">
              <Share2 className="w-6 h-6 text-accent mx-auto mb-2" />
              <p className="text-sm font-medium">3 ways to share</p>
              <p className="text-xs text-muted-foreground">PDF, email, or link</p>
            </div>
          </motion.div>
        </div>
      </SectionWrapper>

      <SectionWrapper background="muted">
        <div className="grid md:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2 }}
            className="glass rounded-xl border border-border p-8 text-center"
          >
            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <BarChart3 className="w-7 h-7 text-primary" />
            </div>
            <h3 className="font-display font-bold text-2xl mb-3">Accurate MLS data</h3>
            <p className="text-muted-foreground leading-relaxed">
              Real-time integration with MLS feeds nationwide for the most current market information
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.05 }}
            className="glass rounded-xl border border-border p-8 text-center"
          >
            <div className="w-14 h-14 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-4">
              <Palette className="w-7 h-7 text-accent" />
            </div>
            <h3 className="font-display font-bold text-2xl mb-3">Branded for you</h3>
            <p className="text-muted-foreground leading-relaxed">
              Add your logo, colors, and contact info once. Every report reflects your professional brand
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.1 }}
            className="glass rounded-xl border border-border p-8 text-center"
          >
            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Download className="w-7 h-7 text-primary" />
            </div>
            <h3 className="font-display font-bold text-2xl mb-3">Print-perfect PDFs</h3>
            <p className="text-muted-foreground leading-relaxed">
              High-resolution exports optimized for digital sharing or professional printing
            </p>
          </motion.div>
        </div>
      </SectionWrapper>

      <SectionWrapper>
        <div className="text-center mb-12">
          <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-balance">How It Works</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            From data to delivery in four simple steps
          </p>
        </div>
        <div className="max-w-4xl mx-auto">
          <Stepper steps={steps} currentStep={2} />
        </div>
        <div className="mt-12 grid md:grid-cols-4 gap-4 max-w-5xl mx-auto">
          <div className="glass rounded-xl border border-border p-6 text-center">
            <MapPin className="w-8 h-8 text-primary mx-auto mb-3" />
            <p className="text-sm font-medium">Select Location</p>
          </div>
          <div className="glass rounded-xl border border-border p-6 text-center">
            <FileText className="w-8 h-8 text-primary mx-auto mb-3" />
            <p className="text-sm font-medium">Choose Template</p>
          </div>
          <div className="glass rounded-xl border border-border p-6 text-center">
            <Palette className="w-8 h-8 text-primary mx-auto mb-3" />
            <p className="text-sm font-medium">Customize Brand</p>
          </div>
          <div className="glass rounded-xl border border-border p-6 text-center">
            <div className="flex gap-2 justify-center mb-3">
              <Download className="w-6 h-6 text-primary" />
              <Mail className="w-6 h-6 text-primary" />
              <Link2 className="w-6 h-6 text-primary" />
            </div>
            <p className="text-sm font-medium">Share Anywhere</p>
          </div>
        </div>
      </SectionWrapper>

      <SectionWrapper background="muted" id="partners">
        <div className="text-center mb-12">
          <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-balance">Title Partners</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Empower your agent network with white-labeled market intelligence
          </p>
        </div>
        <FeatureGrid columns={2}>
          <FeatureCard
            icon={<Users className="w-6 h-6 text-white" />}
            title="Sponsorships"
            description="Sponsor agent reports with your branding. Build relationships and generate qualified leads from every report shared."
            index={0}
          />
          <FeatureCard
            icon={<FileCheck className="w-6 h-6 text-white" />}
            title="Co-branded PDFs"
            description="Your logo alongside agent branding on every report. Increase visibility and reinforce partnerships."
            index={1}
          />
          <FeatureCard
            icon={<DollarSign className="w-6 h-6 text-white" />}
            title="Credits & Ledger"
            description="Flexible credit system with detailed usage tracking. Manage agent allocations and monitor ROI effortlessly."
            index={2}
          />
          <FeatureCard
            icon={<BarChart3 className="w-6 h-6 text-white" />}
            title="Admin Console"
            description="Centralized dashboard to manage agents, track report generation, and analyze engagement metrics."
            index={3}
          />
        </FeatureGrid>
        <div className="text-center mt-12">
          <Button size="lg" className="bg-accent hover:bg-accent/90 text-lg px-8">
            Become a Partner
          </Button>
        </div>
      </SectionWrapper>

      <SectionWrapper id="samples">
        <div className="text-center mb-12">
          <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-balance">Sample Reports</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Explore our professionally designed report templates
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {sampleReports.map((report, index) => (
            <div key={report.id} onClick={() => setSelectedSample(report.id)} className="cursor-pointer">
              <ReportThumbnail title={report.title} date={report.date} imageUrl={report.image} index={index} />
            </div>
          ))}
        </div>

        <Dialog open={selectedSample !== null} onOpenChange={() => setSelectedSample(null)}>
          <DialogContent className="max-w-4xl h-[80vh]">
            <DialogHeader>
              <DialogTitle className="font-display text-2xl">
                {sampleReports.find((r) => r.id === selectedSample)?.title}
              </DialogTitle>
            </DialogHeader>
            <div className="flex-1 bg-muted rounded-lg flex items-center justify-center">
              <p className="text-muted-foreground">Report preview for /print/{selectedSample} would load here</p>
            </div>
          </DialogContent>
        </Dialog>
      </SectionWrapper>

      <SectionWrapper background="muted" id="developers">
        <div className="text-center mb-12">
          <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-balance">Developers & API</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Integrate market reports directly into your applications
          </p>
        </div>
        <div className="max-w-4xl mx-auto space-y-8">
          <div>
            <h3 className="font-display font-semibold text-xl mb-4">POST /v1/reports</h3>
            <CodeTabs pythonCode={pythonCode} javascriptCode={javascriptCode} />
          </div>
          <div>
            <h3 className="font-display font-semibold text-xl mb-4">GET /v1/reports/:id</h3>
            <CodeTabs pythonCode={pythonCodeGet} javascriptCode={javascriptCodeGet} />
          </div>
        </div>
        <div className="text-center mt-8">
          <Button variant="outline" size="lg">
            View Full API Documentation
          </Button>
        </div>
      </SectionWrapper>

      <SectionWrapper id="pricing">
        <div className="text-center mb-12">
          <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-balance">Simple, Transparent Pricing</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Choose the plan that fits your business
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2 }}
            className="glass rounded-xl border border-border p-8"
          >
            <h3 className="font-display font-bold text-2xl mb-2">Starter</h3>
            <div className="mb-6">
              <span className="font-display font-bold text-5xl">$99</span>
              <span className="text-muted-foreground">/month</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">50 reports/month</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Basic branding</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">PDF export</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Email support</span>
              </li>
            </ul>
            <Button variant="outline" className="w-full bg-transparent">
              Start Trial
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.05 }}
            className="glass rounded-xl border-2 border-primary p-8 relative"
          >
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground px-4 py-1 rounded-full text-sm font-semibold">
              Popular
            </div>
            <h3 className="font-display font-bold text-2xl mb-2">Professional</h3>
            <div className="mb-6">
              <span className="font-display font-bold text-5xl">$299</span>
              <span className="text-muted-foreground">/month</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">200 reports/month</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Full branding control</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">All report types</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">API access</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Priority support</span>
              </li>
            </ul>
            <Button className="w-full bg-primary hover:bg-primary/90">Start Trial</Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.1 }}
            className="glass rounded-xl border border-border p-8"
          >
            <h3 className="font-display font-bold text-2xl mb-2">Enterprise</h3>
            <div className="mb-6">
              <span className="font-display font-bold text-5xl">$999</span>
              <span className="text-muted-foreground">/month</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Unlimited reports</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Team management</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Custom templates</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Advanced analytics</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Dedicated support</span>
              </li>
            </ul>
            <Button variant="outline" className="w-full bg-transparent">
              Start Trial
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.15 }}
            className="glass rounded-xl border border-accent p-8"
          >
            <h3 className="font-display font-bold text-2xl mb-2">Title Partner</h3>
            <div className="mb-6">
              <span className="font-display font-bold text-4xl">Contact</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-accent shrink-0 mt-0.5" />
                <span className="text-sm">Agent sponsorships</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-accent shrink-0 mt-0.5" />
                <span className="text-sm">Co-branded reports</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-accent shrink-0 mt-0.5" />
                <span className="text-sm">Credit management</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-accent shrink-0 mt-0.5" />
                <span className="text-sm">Admin console</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-accent shrink-0 mt-0.5" />
                <span className="text-sm">White-label options</span>
              </li>
            </ul>
            <Button variant="outline" className="w-full border-accent text-accent hover:bg-accent/10 bg-transparent">
              Contact Sales
            </Button>
          </motion.div>
        </div>
      </SectionWrapper>

      <SectionWrapper background="muted">
        <div className="glass rounded-xl border border-border p-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                <Shield className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h3 className="font-display font-bold text-xl mb-1">Security & Compliance</h3>
                <p className="text-sm text-muted-foreground">
                  Enterprise-grade security with SOC 2 Type II, GDPR, and CCPA compliance
                </p>
              </div>
            </div>
            <div className="flex items-center gap-6 shrink-0">
              <div className="text-center">
                <div className="font-display font-bold text-2xl">256-bit</div>
                <div className="text-xs text-muted-foreground">Encryption</div>
              </div>
              <div className="text-center">
                <div className="font-display font-bold text-2xl">SOC 2</div>
                <div className="text-xs text-muted-foreground">Type II</div>
              </div>
              <div className="text-center">
                <div className="font-display font-bold text-2xl">99.9%</div>
                <div className="text-xs text-muted-foreground">Uptime</div>
              </div>
            </div>
          </div>
        </div>
      </SectionWrapper>

      <SectionWrapper>
        <div className="text-center mb-12">
          <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-balance">Trusted by Industry Leaders</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            See what real estate professionals are saying
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          <TestimonialCard
            quote="These reports have transformed how we present market data to clients. The branding options are incredible and our close rate has increased by 40%."
            author="Sarah Mitchell"
            role="Senior Real Estate Agent"
            company="Compass Realty"
            rating={5}
            index={0}
          />
          <TestimonialCard
            quote="As a brokerage owner, the Title Partner program has been a game-changer. We sponsor 200+ agents and the ROI is phenomenal."
            author="David Chen"
            role="CEO"
            company="Pacific Title Company"
            rating={5}
            index={1}
          />
          <TestimonialCard
            quote="The API integration was seamless. We now generate custom reports for our clients automatically. Saves us 20+ hours per week."
            author="Jennifer Rodriguez"
            role="CTO"
            company="HomeMatch Technologies"
            rating={5}
            index={2}
          />
        </div>
      </SectionWrapper>

      <SectionWrapper background="gradient" className="py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.2 }}
          className="text-center max-w-4xl mx-auto"
        >
          <h2 className="font-display font-bold text-4xl sm:text-5xl lg:text-6xl mb-6 text-balance">
            Start delivering beautiful, data-driven market reports today.
          </h2>
          <p className="text-xl text-muted-foreground mb-8 text-pretty leading-relaxed">
            Join thousands of agents, brokerages, and title companies transforming their market intelligence
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" className="bg-primary hover:bg-primary/90 text-lg px-8">
              Start Free Trial
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8 bg-transparent">
              Schedule a Demo
            </Button>
          </div>
          <p className="text-sm text-muted-foreground mt-6">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </motion.div>
      </SectionWrapper>

      <Footer />
    </div>
  )
}
