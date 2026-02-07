"use client";

import { useMemo, useState } from "react";
import {
  Plus,
  Upload,
  Search,
  MoreHorizontal,
  UserPlus,
  Users,
  Trash2,
  Pencil,
  Send,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";

import {
  type Contact,
  type ContactType,
  type Group,
  INITIAL_CONTACTS,
  INITIAL_GROUPS,
  getInitials,
  getAvatarColor,
  getTypeColor,
} from "./data";
import { ContactModal } from "./contact-modal";
import { GroupSheet } from "./group-sheet";
import { ImportModal } from "./import-modal";
import { DeleteDialog } from "./delete-dialog";

type TypeFilter = "all" | ContactType;

export default function PeoplePage() {
  // ── Core state ──
  const [contacts, setContacts] = useState<Contact[]>(INITIAL_CONTACTS);
  const [groups, setGroups] = useState<Group[]>(INITIAL_GROUPS);

  // ── UI state ──
  const [activeTab, setActiveTab] = useState("people");
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // ── Modal/sheet/dialog state ──
  const [contactModalOpen, setContactModalOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [groupSheetOpen, setGroupSheetOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);
  const [groupSheetPreSelected, setGroupSheetPreSelected] = useState<string[]>(
    []
  );
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteTargetIds, setDeleteTargetIds] = useState<string[]>([]);
  const [addToGroupPopoverOpen, setAddToGroupPopoverOpen] = useState(false);
  const [groupSearchPopover, setGroupSearchPopover] = useState("");

  // ── Derived data ──
  const filteredContacts = useMemo(() => {
    let list = contacts;
    if (typeFilter !== "all") {
      list = list.filter((c) => c.type === typeFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.email.toLowerCase().includes(q)
      );
    }
    return list;
  }, [contacts, typeFilter, search]);

  const typeCounts = useMemo(() => {
    const counts = { client: 0, agent: 0, list: 0 };
    for (const c of contacts) counts[c.type]++;
    return counts;
  }, [contacts]);

  const allVisibleSelected =
    filteredContacts.length > 0 &&
    filteredContacts.every((c) => selectedIds.has(c.id));

  // ── Helpers ──
  const getGroupsForContact = (c: Contact) =>
    groups.filter((g) => c.groupIds.includes(g.id));

  const nextId = (prefix: string) =>
    `${prefix}${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;

  // ── Selection actions ──
  const toggleSelectAll = () => {
    if (allVisibleSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredContacts.map((c) => c.id)));
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const clearSelection = () => setSelectedIds(new Set());

  // ── Contact CRUD ──
  const handleSaveContact = (data: {
    name: string;
    email: string;
    phone: string;
    type: ContactType;
    groupIds: string[];
  }) => {
    if (editingContact) {
      setContacts((prev) =>
        prev.map((c) =>
          c.id === editingContact.id ? { ...c, ...data } : c
        )
      );
      setGroups((prev) =>
        prev.map((g) => {
          const shouldHave = data.groupIds.includes(g.id);
          const has = g.memberIds.includes(editingContact.id);
          if (shouldHave && !has)
            return { ...g, memberIds: [...g.memberIds, editingContact.id] };
          if (!shouldHave && has)
            return {
              ...g,
              memberIds: g.memberIds.filter((id) => id !== editingContact.id),
            };
          return g;
        })
      );
      toast.success(`${data.name} updated`);
    } else {
      const id = nextId("c");
      setContacts((prev) => [...prev, { id, ...data }]);
      setGroups((prev) =>
        prev.map((g) =>
          data.groupIds.includes(g.id)
            ? { ...g, memberIds: [...g.memberIds, id] }
            : g
        )
      );
      toast.success(`${data.name} added`);
    }
    setContactModalOpen(false);
    setEditingContact(null);
  };

  const handleDeleteContacts = () => {
    setContacts((prev) => prev.filter((c) => !deleteTargetIds.includes(c.id)));
    setGroups((prev) =>
      prev.map((g) => ({
        ...g,
        memberIds: g.memberIds.filter((id) => !deleteTargetIds.includes(id)),
      }))
    );
    const count = deleteTargetIds.length;
    toast.success(
      `${count} contact${count > 1 ? "s" : ""} deleted`
    );
    setDeleteDialogOpen(false);
    setDeleteTargetIds([]);
    setSelectedIds((prev) => {
      const next = new Set(prev);
      for (const id of deleteTargetIds) next.delete(id);
      return next;
    });
  };

  const openDeleteSingle = (c: Contact) => {
    setDeleteTargetIds([c.id]);
    setDeleteDialogOpen(true);
  };

  const openDeleteBulk = () => {
    setDeleteTargetIds(Array.from(selectedIds));
    setDeleteDialogOpen(true);
  };

  // ── Bulk add to group ──
  const handleBulkAddToGroup = (groupId: string) => {
    const ids = Array.from(selectedIds);
    setContacts((prev) =>
      prev.map((c) =>
        ids.includes(c.id) && !c.groupIds.includes(groupId)
          ? { ...c, groupIds: [...c.groupIds, groupId] }
          : c
      )
    );
    setGroups((prev) =>
      prev.map((g) =>
        g.id === groupId
          ? {
              ...g,
              memberIds: [
                ...g.memberIds,
                ...ids.filter((id) => !g.memberIds.includes(id)),
              ],
            }
          : g
      )
    );
    const group = groups.find((g) => g.id === groupId);
    toast.success(`${ids.length} contacts added to ${group?.name}`);
    setAddToGroupPopoverOpen(false);
    clearSelection();
  };

  const handleBulkCreateGroup = () => {
    setGroupSheetPreSelected(Array.from(selectedIds));
    setEditingGroup(null);
    setGroupSheetOpen(true);
    setAddToGroupPopoverOpen(false);
  };

  // ── Group CRUD ──
  const handleSaveGroup = (data: {
    name: string;
    description: string;
    memberIds: string[];
  }) => {
    if (editingGroup) {
      setGroups((prev) =>
        prev.map((g) =>
          g.id === editingGroup.id ? { ...g, ...data } : g
        )
      );
      setContacts((prev) =>
        prev.map((c) => {
          const shouldBeMember = data.memberIds.includes(c.id);
          const isMember = c.groupIds.includes(editingGroup.id);
          if (shouldBeMember && !isMember)
            return { ...c, groupIds: [...c.groupIds, editingGroup.id] };
          if (!shouldBeMember && isMember)
            return {
              ...c,
              groupIds: c.groupIds.filter((id) => id !== editingGroup.id),
            };
          return c;
        })
      );
      toast.success(`${data.name} updated`);
    } else {
      const id = nextId("g");
      setGroups((prev) => [
        ...prev,
        { id, ...data, createdAt: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) },
      ]);
      setContacts((prev) =>
        prev.map((c) =>
          data.memberIds.includes(c.id)
            ? { ...c, groupIds: [...c.groupIds, id] }
            : c
        )
      );
      toast.success(`${data.name} created with ${data.memberIds.length} members`);
    }
    setGroupSheetOpen(false);
    setEditingGroup(null);
    setGroupSheetPreSelected([]);
    clearSelection();
  };

  const handleDeleteGroup = (g: Group) => {
    setGroups((prev) => prev.filter((gr) => gr.id !== g.id));
    setContacts((prev) =>
      prev.map((c) => ({
        ...c,
        groupIds: c.groupIds.filter((id) => id !== g.id),
      }))
    );
    toast.success(`${g.name} deleted`);
  };

  // ── Import ──
  const handleImport = (
    rows: { name: string; email: string; phone: string }[],
    type: ContactType,
    groupId: string | null
  ) => {
    const newContacts: Contact[] = rows.map((r) => ({
      id: nextId("c"),
      name: r.name,
      email: r.email,
      phone: r.phone,
      type,
      groupIds: groupId ? [groupId] : [],
    }));
    setContacts((prev) => [...prev, ...newContacts]);
    if (groupId) {
      const newIds = newContacts.map((c) => c.id);
      setGroups((prev) =>
        prev.map((g) =>
          g.id === groupId
            ? { ...g, memberIds: [...g.memberIds, ...newIds] }
            : g
        )
      );
    }
    toast.success(`${rows.length} contacts imported`);
  };

  // ── Popover filtered groups ──
  const popoverGroups = groups.filter((g) =>
    g.name.toLowerCase().includes(groupSearchPopover.toLowerCase())
  );

  const deleteNames = deleteTargetIds
    .map((id) => contacts.find((c) => c.id === id)?.name ?? "")
    .filter(Boolean);

  return (
    <div className="mx-auto max-w-[960px] px-6 py-10">
      {/* ── Page header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">People</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your contacts and groups
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setImportModalOpen(true)}
          >
            <Upload className="mr-2 h-4 w-4" />
            Import CSV
          </Button>
          <Button
            size="sm"
            className="bg-[#6366F1] text-white hover:bg-[#4F46E5]"
            onClick={() => {
              setEditingContact(null);
              setContactModalOpen(true);
            }}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add
          </Button>
        </div>
      </div>

      {/* ── Tabs + search row ── */}
      <div className="mt-6 flex items-center justify-between gap-4">
        <Tabs
          value={activeTab}
          onValueChange={(v) => {
            setActiveTab(v);
            clearSelection();
          }}
        >
          <TabsList>
            <TabsTrigger value="people">
              People ({contacts.length})
            </TabsTrigger>
            <TabsTrigger value="groups">
              Groups ({groups.length})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {activeTab === "people" && (
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="pl-9 h-9"
            />
          </div>
        )}
      </div>

      {/* ── People tab ── */}
      {activeTab === "people" && (
        <div className="mt-4">
          {/* Selection bar OR filter chips */}
          {selectedIds.size > 0 ? (
            <div className="flex items-center gap-3 rounded-lg bg-[#6366F1] px-4 py-2.5 text-white animate-in slide-in-from-top-2 duration-200">
              <span className="text-sm font-medium">
                {selectedIds.size} selected
              </span>
              <div className="ml-auto flex items-center gap-2">
                <Popover
                  open={addToGroupPopoverOpen}
                  onOpenChange={setAddToGroupPopoverOpen}
                >
                  <PopoverTrigger asChild>
                    <Button
                      size="sm"
                      variant="secondary"
                      className="h-8 bg-white/20 text-white hover:bg-white/30 border-0"
                    >
                      <UserPlus className="mr-1.5 h-3.5 w-3.5" />
                      Add to Group
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[280px] p-0" align="end">
                    <div className="p-3">
                      <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                        <Input
                          value={groupSearchPopover}
                          onChange={(e) =>
                            setGroupSearchPopover(e.target.value)
                          }
                          placeholder="Search groups..."
                          className="pl-8 h-8 text-sm"
                        />
                      </div>
                    </div>
                    <ScrollArea className="max-h-[200px]">
                      <div className="px-1 pb-1">
                        {popoverGroups.map((g) => (
                          <button
                            type="button"
                            key={g.id}
                            onClick={() => handleBulkAddToGroup(g.id)}
                            className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-muted transition-colors"
                          >
                            <span className="text-foreground">{g.name}</span>
                            <span className="text-xs text-muted-foreground">
                              {g.memberIds.length}
                            </span>
                          </button>
                        ))}
                        {popoverGroups.length === 0 && (
                          <p className="px-3 py-4 text-center text-sm text-muted-foreground">
                            No groups found
                          </p>
                        )}
                      </div>
                    </ScrollArea>
                    <div className="border-t p-1">
                      <button
                        type="button"
                        onClick={handleBulkCreateGroup}
                        className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-[#6366F1] hover:bg-muted transition-colors"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Create New Group
                      </button>
                    </div>
                  </PopoverContent>
                </Popover>
                <Button
                  size="sm"
                  variant="secondary"
                  className="h-8 bg-white/20 text-white hover:bg-white/30 border-0"
                  onClick={openDeleteBulk}
                >
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                  Remove
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 text-white hover:bg-white/20"
                  onClick={clearSelection}
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Clear selection</span>
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              {(
                [
                  { key: "all" as TypeFilter, label: "All" },
                  {
                    key: "client" as TypeFilter,
                    label: `Clients (${typeCounts.client})`,
                  },
                  {
                    key: "agent" as TypeFilter,
                    label: `Agents (${typeCounts.agent})`,
                  },
                  {
                    key: "list" as TypeFilter,
                    label: `Lists (${typeCounts.list})`,
                  },
                ] as const
              ).map((f) => (
                <button
                  key={f.key}
                  type="button"
                  onClick={() => setTypeFilter(f.key)}
                  className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors ${
                    typeFilter === f.key
                      ? "bg-[#6366F1] text-white"
                      : "bg-muted text-muted-foreground hover:bg-[#E0E7FF] hover:text-foreground"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          )}

          {/* ── Table ── */}
          <div className="mt-4 rounded-lg border">
            {/* Header */}
            <div className="grid grid-cols-[40px_1fr_1fr_140px_80px_120px_40px] items-center gap-2 border-b bg-muted/40 px-3 py-2.5 text-xs font-medium text-muted-foreground">
              <div className="flex items-center justify-center">
                <Checkbox
                  checked={allVisibleSelected}
                  onCheckedChange={toggleSelectAll}
                  aria-label="Select all"
                />
              </div>
              <div>Name</div>
              <div>Email</div>
              <div>Phone</div>
              <div>Type</div>
              <div>Groups</div>
              <div />
            </div>

            {/* Rows */}
            {filteredContacts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <Users className="h-10 w-10 mb-3 text-muted-foreground/50" />
                <p className="text-sm font-medium">No contacts found</p>
                <p className="text-xs mt-1">
                  {search
                    ? "Try a different search term"
                    : "Add your first contact to get started"}
                </p>
              </div>
            ) : (
              filteredContacts.map((c) => {
                const cGroups = getGroupsForContact(c);
                const typeCol = getTypeColor(c.type);
                return (
                  <div
                    key={c.id}
                    className={`grid grid-cols-[40px_1fr_1fr_140px_80px_120px_40px] items-center gap-2 border-b last:border-b-0 px-3 py-2.5 transition-colors hover:bg-muted/30 ${
                      selectedIds.has(c.id) ? "bg-[#EEF2FF]" : ""
                    }`}
                  >
                    <div className="flex items-center justify-center">
                      <Checkbox
                        checked={selectedIds.has(c.id)}
                        onCheckedChange={() => toggleSelect(c.id)}
                        aria-label={`Select ${c.name}`}
                      />
                    </div>
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${getAvatarColor(c.type)}`}
                      >
                        {getInitials(c.name)}
                      </div>
                      <span className="text-sm font-medium text-foreground truncate">
                        {c.name}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground truncate">
                      {c.email}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {c.phone || "—"}
                    </div>
                    <div>
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${typeCol.bg} ${typeCol.text}`}
                      >
                        {c.type}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 min-w-0 overflow-hidden">
                      {cGroups.length === 0 && (
                        <span className="text-sm text-muted-foreground">
                          —
                        </span>
                      )}
                      {cGroups.slice(0, 2).map((g) => (
                        <span
                          key={g.id}
                          className="inline-flex shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
                        >
                          {g.name}
                        </span>
                      ))}
                      {cGroups.length > 2 && (
                        <span className="shrink-0 text-[10px] text-muted-foreground">
                          +{cGroups.length - 2}
                        </span>
                      )}
                    </div>
                    <div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">Actions</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-[160px]">
                          <DropdownMenuItem
                            onClick={() => {
                              setEditingContact(c);
                              setContactModalOpen(true);
                            }}
                          >
                            <Pencil className="mr-2 h-3.5 w-3.5" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              setSelectedIds(new Set([c.id]));
                              setAddToGroupPopoverOpen(true);
                            }}
                          >
                            <UserPlus className="mr-2 h-3.5 w-3.5" />
                            Add to Group
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => openDeleteSingle(c)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="mr-2 h-3.5 w-3.5" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer count */}
          {filteredContacts.length > 0 && (
            <p className="mt-3 text-xs text-muted-foreground">
              Showing {filteredContacts.length} of {contacts.length} contacts
            </p>
          )}
        </div>
      )}

      {/* ── Groups tab ── */}
      {activeTab === "groups" && (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {groups.map((g) => {
            const members = contacts.filter((c) =>
              g.memberIds.includes(c.id)
            );
            return (
              <div
                key={g.id}
                className="group relative cursor-pointer rounded-xl border bg-card p-5 transition-shadow hover:shadow-md"
                onClick={() => {
                  setEditingGroup(g);
                  setGroupSheetPreSelected([]);
                  setGroupSheetOpen(true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    setEditingGroup(g);
                    setGroupSheetPreSelected([]);
                    setGroupSheetOpen(true);
                  }
                }}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">
                      {g.name}
                    </h3>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {g.memberIds.length} contacts
                    </p>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreHorizontal className="h-4 w-4" />
                        <span className="sr-only">Group actions</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-[170px]">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingGroup(g);
                          setGroupSheetPreSelected([]);
                          setGroupSheetOpen(true);
                        }}
                      >
                        <Pencil className="mr-2 h-3.5 w-3.5" />
                        Edit Group
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingGroup(g);
                          setGroupSheetPreSelected([]);
                          setGroupSheetOpen(true);
                        }}
                      >
                        <Users className="mr-2 h-3.5 w-3.5" />
                        Manage Members
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          toast.success(
                            `Report queued for ${g.memberIds.length} contacts`
                          );
                        }}
                      >
                        <Send className="mr-2 h-3.5 w-3.5" />
                        Send Report
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteGroup(g);
                        }}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-3.5 w-3.5" />
                        Delete Group
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Avatar stack */}
                <div className="mt-4 flex items-center">
                  {members.slice(0, 3).map((m, i) => (
                    <div
                      key={m.id}
                      className={`flex h-7 w-7 items-center justify-center rounded-full border-2 border-card text-[10px] font-bold ${getAvatarColor(m.type)} ${i > 0 ? "-ml-2" : ""}`}
                    >
                      {getInitials(m.name)}
                    </div>
                  ))}
                  {members.length > 3 && (
                    <div className="-ml-2 flex h-7 w-7 items-center justify-center rounded-full border-2 border-card bg-muted text-[10px] font-medium text-muted-foreground">
                      +{members.length - 3}
                    </div>
                  )}
                  {members.length === 0 && (
                    <span className="text-xs text-muted-foreground">
                      No members yet
                    </span>
                  )}
                </div>

                <p className="mt-3 text-[11px] text-muted-foreground">
                  Created {g.createdAt}
                </p>
              </div>
            );
          })}

          {/* + New Group card */}
          <button
            type="button"
            onClick={() => {
              setEditingGroup(null);
              setGroupSheetPreSelected([]);
              setGroupSheetOpen(true);
            }}
            className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border p-5 text-muted-foreground transition-colors hover:border-[#6366F1] hover:text-[#6366F1] min-h-[160px]"
          >
            <Plus className="h-8 w-8 mb-2" />
            <span className="text-sm font-medium">New Group</span>
          </button>
        </div>
      )}

      {/* ── Modals / Sheets / Dialogs ── */}
      <ContactModal
        open={contactModalOpen}
        onOpenChange={(v) => {
          setContactModalOpen(v);
          if (!v) setEditingContact(null);
        }}
        contact={editingContact}
        groups={groups}
        onSave={handleSaveContact}
      />

      <GroupSheet
        open={groupSheetOpen}
        onOpenChange={(v) => {
          setGroupSheetOpen(v);
          if (!v) {
            setEditingGroup(null);
            setGroupSheetPreSelected([]);
          }
        }}
        group={editingGroup}
        contacts={contacts}
        preSelectedIds={groupSheetPreSelected}
        onSave={handleSaveGroup}
      />

      <ImportModal
        open={importModalOpen}
        onOpenChange={setImportModalOpen}
        groups={groups}
        existingEmails={contacts.map((c) => c.email.toLowerCase())}
        onImport={handleImport}
      />

      <DeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        contactNames={deleteNames}
        onConfirm={handleDeleteContacts}
      />
    </div>
  );
}
