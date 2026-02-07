export type ContactType = "client" | "agent" | "list";

export interface Contact {
  id: string;
  name: string;
  email: string;
  phone: string;
  type: ContactType;
  groupIds: string[];
}

export interface Group {
  id: string;
  name: string;
  description: string;
  memberIds: string[];
  createdAt: string;
}

export const INITIAL_CONTACTS: Contact[] = [
  {
    id: "c1",
    name: "Sarah Chen",
    email: "sarah@acmerealty.com",
    phone: "(310) 555-0142",
    type: "client",
    groupIds: ["g1", "g5"],
  },
  {
    id: "c2",
    name: "James Wilson",
    email: "james@wilson.net",
    phone: "(424) 555-0198",
    type: "client",
    groupIds: ["g2"],
  },
  {
    id: "c3",
    name: "Maria Rodriguez",
    email: "maria@rodriguez.com",
    phone: "(818) 555-0167",
    type: "client",
    groupIds: ["g3", "g1"],
  },
  {
    id: "c4",
    name: "David Kim",
    email: "david@compass.com",
    phone: "(310) 555-0234",
    type: "agent",
    groupIds: ["g4"],
  },
  {
    id: "c5",
    name: "Lisa Park",
    email: "lisa@kw.com",
    phone: "(626) 555-0189",
    type: "agent",
    groupIds: ["g4"],
  },
  {
    id: "c6",
    name: "Alex Thompson",
    email: "alex@coldwell.com",
    phone: "(323) 555-0156",
    type: "agent",
    groupIds: ["g4"],
  },
  {
    id: "c7",
    name: "Buyer Leads LA",
    email: "buyers-la@lists.acme.com",
    phone: "",
    type: "list",
    groupIds: ["g3"],
  },
  {
    id: "c8",
    name: "Investor Circle",
    email: "investors@lists.acme.com",
    phone: "",
    type: "list",
    groupIds: [],
  },
  {
    id: "c9",
    name: "Tom Martinez",
    email: "tom@martinez.io",
    phone: "(562) 555-0211",
    type: "client",
    groupIds: ["g2", "g3"],
  },
  {
    id: "c10",
    name: "Rachel Green",
    email: "rachel@douglas.com",
    phone: "(213) 555-0178",
    type: "client",
    groupIds: ["g5"],
  },
  {
    id: "c11",
    name: "Kevin Nguyen",
    email: "kevin@remax.com",
    phone: "(714) 555-0145",
    type: "agent",
    groupIds: [],
  },
  {
    id: "c12",
    name: "Open House List",
    email: "openhouse@lists.acme.com",
    phone: "",
    type: "list",
    groupIds: ["g3"],
  },
];

export const INITIAL_GROUPS: Group[] = [
  {
    id: "g1",
    name: "Luxury Buyers",
    description: "High-end property buyers in the LA area",
    memberIds: ["c1", "c3"],
    createdAt: "Jan 15, 2026",
  },
  {
    id: "g2",
    name: "First-Time Buyers",
    description: "New buyers looking for starter homes",
    memberIds: ["c2", "c9"],
    createdAt: "Jan 20, 2026",
  },
  {
    id: "g3",
    name: "Monthly Newsletter",
    description: "All contacts receiving the monthly report",
    memberIds: ["c3", "c7", "c9", "c12"],
    createdAt: "Dec 1, 2025",
  },
  {
    id: "g4",
    name: "Agents Network",
    description: "Partnered agents and brokerages",
    memberIds: ["c4", "c5", "c6"],
    createdAt: "Nov 15, 2025",
  },
  {
    id: "g5",
    name: "VIP Clients",
    description: "Top-tier clients with priority service",
    memberIds: ["c1", "c10"],
    createdAt: "Feb 1, 2026",
  },
];

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function getTypeColor(type: ContactType) {
  switch (type) {
    case "client":
      return { bg: "bg-[#EEF2FF]", text: "text-[#4338CA]" };
    case "agent":
      return { bg: "bg-[#F1F5F9]", text: "text-[#334155]" };
    case "list":
      return { bg: "bg-[#F8FAFC]", text: "text-[#64748B]" };
  }
}

export function getAvatarColor(type: ContactType) {
  switch (type) {
    case "client":
      return "bg-[#6366F1] text-white";
    case "agent":
      return "bg-[#334155] text-white";
    case "list":
      return "bg-[#94A3B8] text-white";
  }
}
