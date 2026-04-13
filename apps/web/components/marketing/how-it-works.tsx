"use client";

import { motion } from "framer-motion";
import {
  MapPin,
  Palette,
  Send,
  Check,
  ChevronDown,
  Search,
  Upload,
  Calendar,
  Mail,
  Users,
  Clock,
  Home,
  DollarSign,
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: "easeOut" } },
};

function CitySearchMockup() {
  const cities = [
    { name: "Irvine", count: "2,847 listings", active: true },
    { name: "Newport Beach", count: "1,432 listings", active: false },
    { name: "Pasadena", count: "1,891 listings", active: false },
    { name: "Laguna Beach", count: "876 listings", active: false },
  ];

  const reportTypes = [
    { name: "Market Snapshot", icon: Home, selected: true },
    { name: "New Listings", icon: DollarSign, selected: false },
    { name: "Closed Sales", icon: Check, selected: false },
  ];

  return (
    <motion.div
      variants={scaleIn}
      className="relative mx-auto w-full max-w-xl overflow-hidden rounded-2xl bg-white shadow-2xl shadow-[#6366F1]/10 ring-1 ring-[#E2E8F0]"
      whileHover={{ scale: 1.02, transition: { duration: 0.3 } }}
    >
      <div className="flex items-center justify-between border-b border-[#F1F5F9] bg-[#FAFBFC] px-5 py-3">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-[#FCA5A5]" />
          <div className="h-3 w-3 rounded-full bg-[#FCD34D]" />
          <div className="h-3 w-3 rounded-full bg-[#86EFAC]" />
        </div>
        <span className="text-xs font-medium text-[#94A3B8]">Create New Report</span>
        <div className="w-12" />
      </div>

      <div className="p-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#94A3B8]" />
          <input
            type="text"
            readOnly
            value="Southern California"
            className="w-full rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] py-3.5 pl-12 pr-4 text-sm font-medium text-[#0F172A] focus:outline-none"
          />
          <ChevronDown className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#94A3B8]" />
        </div>

        <div className="mt-4 space-y-2">
          {cities.map((city) => (
            <div
              key={city.name}
              className={`flex items-center justify-between rounded-xl px-4 py-3 transition-all ${
                city.active
                  ? "bg-[#6366F1] text-white shadow-lg shadow-[#6366F1]/25"
                  : "bg-[#F8FAFC] text-[#64748B] hover:bg-[#F1F5F9]"
              }`}
            >
              <div className="flex items-center gap-3">
                <MapPin className={`h-4 w-4 ${city.active ? "text-white" : "text-[#94A3B8]"}`} />
                <span className="font-medium">{city.name}</span>
              </div>
              <span className={`text-sm ${city.active ? "text-white/80" : "text-[#94A3B8]"}`}>
                {city.count}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <p className="mb-3 text-sm font-medium text-[#64748B]">Report Type</p>
          <div className="grid grid-cols-3 gap-3">
            {reportTypes.map((type) => (
              <div
                key={type.name}
                className={`flex flex-col items-center rounded-xl border-2 px-3 py-4 text-center transition-all ${
                  type.selected
                    ? "border-[#6366F1] bg-[#EEF2FF]"
                    : "border-[#E2E8F0] bg-white hover:border-[#CBD5E1]"
                }`}
              >
                <type.icon
                  className={`h-5 w-5 ${type.selected ? "text-[#6366F1]" : "text-[#94A3B8]"}`}
                />
                <span
                  className={`mt-2 text-xs font-medium ${
                    type.selected ? "text-[#4F46E5]" : "text-[#64748B]"
                  }`}
                >
                  {type.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="absolute -right-3 -top-3 rounded-full bg-[#6366F1] px-4 py-2 text-sm font-bold text-white shadow-lg">
        350+ cities
      </div>
    </motion.div>
  );
}

function BrandingMockup() {
  return (
    <motion.div
      variants={scaleIn}
      className="relative mx-auto w-full max-w-xl overflow-hidden rounded-2xl bg-white shadow-2xl shadow-[#6366F1]/10 ring-1 ring-[#E2E8F0]"
      whileHover={{ scale: 1.02, transition: { duration: 0.3 } }}
    >
      <div className="flex items-center justify-between border-b border-[#F1F5F9] bg-[#FAFBFC] px-5 py-3">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-[#FCA5A5]" />
          <div className="h-3 w-3 rounded-full bg-[#FCD34D]" />
          <div className="h-3 w-3 rounded-full bg-[#86EFAC]" />
        </div>
        <span className="text-xs font-medium text-[#94A3B8]">Brand Settings</span>
        <div className="w-12" />
      </div>

      <div className="flex">
        <div className="w-1/2 border-r border-[#F1F5F9] p-5">
          <div className="mb-5">
            <p className="mb-2 text-sm font-medium text-[#64748B]">Your Logo</p>
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[#6366F1] text-xl font-bold text-white shadow-md">
                JR
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-[#0F172A]">Jennifer Realty</span>
                <button className="flex items-center gap-1 text-xs text-[#6366F1]">
                  <Upload className="h-3 w-3" />
                  Change
                </button>
              </div>
            </div>
          </div>

          <div className="mb-5">
            <p className="mb-2 text-sm font-medium text-[#64748B]">Brand Colors</p>
            <div className="flex gap-2">
              <div className="h-10 w-10 rounded-xl bg-[#6366F1] ring-2 ring-[#6366F1] ring-offset-2" />
              <div className="h-10 w-10 rounded-xl bg-[#0F172A] ring-2 ring-transparent ring-offset-2" />
              <div className="h-10 w-10 rounded-xl bg-white ring-2 ring-[#E2E8F0] ring-offset-2" />
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-dashed border-[#CBD5E1]">
                <span className="text-lg text-[#94A3B8]">+</span>
              </div>
            </div>
          </div>

          <div>
            <p className="mb-2 text-sm font-medium text-[#64748B]">Contact Info</p>
            <div className="space-y-2 text-sm text-[#64748B]">
              <p className="font-medium text-[#0F172A]">Jennifer Martinez</p>
              <p>(949) 555-0123</p>
              <p>jennifer@jenniferrealty.com</p>
            </div>
          </div>
        </div>

        <div className="w-1/2 bg-[#F8FAFC] p-4">
          <p className="mb-2 text-center text-xs font-medium text-[#94A3B8]">Live Preview</p>
          <div className="overflow-hidden rounded-lg bg-white shadow-md">
            <div className="bg-[#6366F1] px-3 py-3">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-white/20 text-xs font-bold text-white">
                  JR
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">Market Snapshot</p>
                  <p className="text-[10px] text-white/70">Irvine, CA</p>
                </div>
              </div>
            </div>
            <div className="p-3">
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: "Median", value: "$1.2M" },
                  { label: "Active", value: "847" },
                  { label: "DOM", value: "24" },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-md bg-[#F8FAFC] p-2 text-center">
                    <p className="text-xs font-bold text-[#0F172A]">{stat.value}</p>
                    <p className="text-[9px] text-[#94A3B8]">{stat.label}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2 border-t border-[#F1F5F9] pt-2">
                <div className="h-6 w-6 rounded-full bg-[#6366F1] text-center text-[10px] font-bold leading-6 text-white">
                  JM
                </div>
                <div>
                  <p className="text-[10px] font-medium text-[#0F172A]">Jennifer Martinez</p>
                  <p className="text-[9px] text-[#94A3B8]">(949) 555-0123</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute -right-3 -top-3 rounded-full bg-[#0F172A] px-4 py-2 text-sm font-bold text-white shadow-lg">
        Your brand
      </div>
    </motion.div>
  );
}

function ScheduleMockup() {
  const recipients = [
    { name: "Irvine Buyers", count: 47, color: "bg-[#6366F1]" },
    { name: "Newport Sellers", count: 32, color: "bg-[#4338CA]" },
    { name: "OC Investors", count: 28, color: "bg-[#818CF8]" },
  ];

  return (
    <motion.div
      variants={scaleIn}
      className="relative mx-auto w-full max-w-xl overflow-hidden rounded-2xl bg-white shadow-2xl shadow-[#6366F1]/10 ring-1 ring-[#E2E8F0]"
      whileHover={{ scale: 1.02, transition: { duration: 0.3 } }}
    >
      <div className="flex items-center justify-between border-b border-[#F1F5F9] bg-[#FAFBFC] px-5 py-3">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-[#FCA5A5]" />
          <div className="h-3 w-3 rounded-full bg-[#FCD34D]" />
          <div className="h-3 w-3 rounded-full bg-[#86EFAC]" />
        </div>
        <span className="text-xs font-medium text-[#94A3B8]">Schedule Delivery</span>
        <div className="w-12" />
      </div>

      <div className="flex">
        <div className="w-1/2 border-r border-[#F1F5F9] p-5">
          <div className="mb-5">
            <p className="mb-2 text-sm font-medium text-[#64748B]">Delivery Frequency</p>
            <div className="flex gap-2">
              <div className="flex items-center gap-2 rounded-xl bg-[#6366F1] px-4 py-2.5 text-sm font-medium text-white shadow-md">
                <Clock className="h-4 w-4" />
                Weekly
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-[#E2E8F0] bg-white px-4 py-2.5 text-sm font-medium text-[#64748B]">
                <Calendar className="h-4 w-4" />
                Monthly
              </div>
            </div>
          </div>

          <div className="mb-5">
            <p className="mb-2 text-sm font-medium text-[#64748B]">Send on</p>
            <div className="flex gap-1">
              {["S", "M", "T", "W", "T", "F", "S"].map((day, i) => (
                <div
                  key={i}
                  className={`flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium ${
                    i === 1
                      ? "bg-[#6366F1] text-white"
                      : "bg-[#F8FAFC] text-[#64748B]"
                  }`}
                >
                  {day}
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-2 text-sm font-medium text-[#64748B]">Recipients</p>
            <div className="space-y-2">
              {recipients.map((group) => (
                <div
                  key={group.name}
                  className="flex items-center justify-between rounded-xl bg-[#F8FAFC] px-3 py-2.5"
                >
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-[#94A3B8]" />
                    <span className="text-sm font-medium text-[#0F172A]">{group.name}</span>
                  </div>
                  <span className="rounded-full bg-[#EEF2FF] px-2 py-0.5 text-xs font-medium text-[#6366F1]">
                    {group.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="w-1/2 bg-[#F8FAFC] p-4">
          <p className="mb-3 text-center text-xs font-medium text-[#94A3B8]">What they receive</p>
          <div className="overflow-hidden rounded-lg bg-white shadow-md">
            <div className="border-b border-[#F1F5F9] px-3 py-2">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-[#6366F1]" />
                <div>
                  <p className="text-[10px] font-medium text-[#0F172A]">New Market Report</p>
                  <p className="text-[9px] text-[#94A3B8]">from Jennifer Martinez</p>
                </div>
              </div>
            </div>
            <div className="p-3">
              <div className="mb-2 h-24 rounded-md bg-gradient-to-br from-[#6366F1] to-[#4338CA]">
                <div className="flex h-full flex-col items-center justify-center text-white">
                  <p className="text-xs font-semibold">Irvine Market Snapshot</p>
                  <p className="text-[10px] opacity-70">March 2026</p>
                </div>
              </div>
              <div className="flex gap-2">
                <div className="flex-1 rounded-md bg-[#F8FAFC] p-2 text-center">
                  <p className="text-xs font-bold text-[#0F172A]">$1.2M</p>
                  <p className="text-[8px] text-[#94A3B8]">Median</p>
                </div>
                <div className="flex-1 rounded-md bg-[#F8FAFC] p-2 text-center">
                  <p className="text-xs font-bold text-[#0F172A]">847</p>
                  <p className="text-[8px] text-[#94A3B8]">Active</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-3 flex items-center gap-2 rounded-lg bg-[#DCFCE7] px-3 py-2">
            <Check className="h-4 w-4 text-[#16A34A]" />
            <div>
              <p className="text-xs font-medium text-[#166534]">Delivered</p>
              <p className="text-[10px] text-[#166534]/70">107 contacts • Mon 9:00 AM</p>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute -right-3 -top-3 rounded-full bg-[#16A34A] px-4 py-2 text-sm font-bold text-white shadow-lg">
        Autopilot
      </div>
    </motion.div>
  );
}

export function HowItWorks() {
  const steps = [
    {
      number: "01",
      icon: MapPin,
      title: "Choose your market",
      description:
        "Select a Southern California city from our database of 350+ markets. Pick your report type, set filters for price range and property type, and we pull the latest MLS data automatically.",
      visual: <CitySearchMockup />,
    },
    {
      number: "02",
      icon: Palette,
      title: "Brand it yours",
      description:
        "Upload your logo, set your brand colors, and add your contact info. Every report automatically carries your branding — your clients see you, not us. Preview changes live before publishing.",
      visual: <BrandingMockup />,
    },
    {
      number: "03",
      icon: Send,
      title: "Set & forget",
      description:
        "Schedule weekly or monthly delivery. Add recipients from your contact groups. We generate fresh reports with the latest MLS data and deliver branded emails to your sphere — automatically.",
      visual: <ScheduleMockup />,
    },
  ];

  return (
    <section id="how-it-works" className="overflow-hidden bg-[#F8FAFC] px-6 py-24 md:py-32">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={{ visible: { transition: { staggerChildren: 0.2 } } }}
      >
        <motion.div variants={fadeUp} className="text-center">
          <span className="inline-block rounded-full bg-[#EEF2FF] px-4 py-1.5 text-sm font-semibold text-[#6366F1]">
            How it works
          </span>
          <h2 className="mt-6 text-4xl font-bold tracking-tight text-[#0F172A] md:text-5xl lg:text-6xl">
            {"From MLS data to your clients' inbox"}
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-[#64748B]">
            Three steps. Two minutes. Zero design skills required.
          </p>
        </motion.div>

        <motion.div variants={fadeUp} className="mt-16 flex items-center justify-center gap-4">
          {[1, 2, 3].map((num, i) => (
            <div key={num} className="flex items-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#6366F1] text-sm font-bold text-white shadow-lg shadow-[#6366F1]/25">
                {num}
              </div>
              {i < 2 && (
                <div className="mx-2 h-0.5 w-16 bg-gradient-to-r from-[#6366F1] to-[#A5B4FC] md:w-24" />
              )}
            </div>
          ))}
        </motion.div>

        <div className="mt-20 space-y-24 md:space-y-32">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              variants={fadeUp}
              className={`flex flex-col items-center gap-12 lg:flex-row lg:gap-16 ${
                index % 2 === 1 ? "lg:flex-row-reverse" : ""
              }`}
            >
              <div className="w-full lg:w-[58%]">{step.visual}</div>

              <div className="w-full text-center lg:w-[42%] lg:text-left">
                <div className="mb-4 flex items-center justify-center gap-4 lg:justify-start">
                  <span className="text-6xl font-bold text-[#E2E8F0] md:text-7xl">
                    {step.number}
                  </span>
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#6366F1] shadow-lg shadow-[#6366F1]/25">
                    <step.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-[#0F172A] md:text-3xl">{step.title}</h3>
                <p className="mt-4 text-lg leading-relaxed text-[#64748B]">{step.description}</p>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div variants={fadeUp} className="mt-24 text-center">
          <a
            href="/register"
            className="inline-flex items-center gap-3 rounded-full bg-[#6366F1] px-10 py-4 text-lg font-semibold text-white shadow-xl shadow-[#6366F1]/25 transition-all hover:bg-[#4F46E5] hover:shadow-2xl hover:shadow-[#6366F1]/30"
          >
            Start your free trial
          </a>
          <p className="mt-4 text-[#64748B]">
            Your first report is ready in under 2 minutes. No credit card required.
          </p>
        </motion.div>
      </motion.div>
    </section>
  );
}
