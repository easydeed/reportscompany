"use client";

import { useEffect, useState } from "react";
import { Search, X } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { Contact, Group } from "./data";
import { getInitials, getAvatarColor } from "./data";

interface GroupSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  group: Group | null;
  contacts: Contact[];
  preSelectedIds?: string[];
  onSave: (data: {
    name: string;
    description: string;
    memberIds: string[];
  }) => void;
}

export function GroupSheet({
  open,
  onOpenChange,
  group,
  contacts,
  preSelectedIds,
  onSave,
}: GroupSheetProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (open) {
      if (group) {
        setName(group.name);
        setDescription(group.description);
        setSelectedIds(group.memberIds);
      } else {
        setName("");
        setDescription("");
        setSelectedIds(preSelectedIds ?? []);
      }
      setSearch("");
    }
  }, [open, group, preSelectedIds]);

  const isEditing = !!group;

  const toggleContact = (cid: string) => {
    setSelectedIds((prev) =>
      prev.includes(cid) ? prev.filter((id) => id !== cid) : [...prev, cid]
    );
  };

  const removeSelected = (cid: string) => {
    setSelectedIds((prev) => prev.filter((id) => id !== cid));
  };

  const filteredContacts = contacts.filter(
    (c) =>
      !selectedIds.includes(c.id) &&
      (c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.email.toLowerCase().includes(search.toLowerCase()))
  );

  const selectedContacts = contacts.filter((c) => selectedIds.includes(c.id));

  const handleSubmit = () => {
    if (!name.trim()) return;
    onSave({
      name: name.trim(),
      description: description.trim(),
      memberIds: selectedIds,
    });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[520px] p-0 flex flex-col">
        <SheetHeader className="p-6 pb-4">
          <SheetTitle>
            {isEditing ? `Edit Group` : "Create Group"}
          </SheetTitle>
          <SheetDescription>
            {isEditing
              ? `Manage members and settings for "${group?.name}".`
              : "Name your group and add members."}
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6">
          <div className="space-y-4">
            <div>
              <Label htmlFor="group-name" className="text-sm font-medium">
                Group Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="group-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Luxury Buyers"
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="group-desc" className="text-sm font-medium">
                Description{" "}
                <span className="text-muted-foreground font-normal">(optional)</span>
              </Label>
              <Input
                id="group-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description..."
                className="mt-1.5"
              />
            </div>
          </div>

          <Separator className="my-5" />

          <div>
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Members</Label>
              <span className="text-xs text-muted-foreground">
                {contacts.length} available
              </span>
            </div>

            <div className="mt-2 relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search contacts..."
                className="pl-9"
              />
            </div>

            {selectedContacts.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Selected ({selectedContacts.length})
                </p>
                <div className="rounded-lg border divide-y">
                  {selectedContacts.map((c) => (
                    <div
                      key={c.id}
                      className="flex items-center gap-3 px-3 py-2.5"
                    >
                      <div
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${getAvatarColor(c.type)}`}
                      >
                        {getInitials(c.name)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-foreground truncate">
                          {c.name}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {c.email}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeSelected(c.id)}
                        className="shrink-0 rounded-md p-1 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <X className="h-3.5 w-3.5" />
                        <span className="sr-only">Remove {c.name}</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 mb-4">
              <p className="text-xs font-medium text-muted-foreground mb-2">
                All Contacts
              </p>
              <ScrollArea className="h-[240px] rounded-lg border">
                <div className="divide-y">
                  {filteredContacts.map((c) => (
                    <label
                      key={c.id}
                      className="flex items-center gap-3 px-3 py-2.5 hover:bg-muted cursor-pointer"
                    >
                      <Checkbox
                        checked={false}
                        onCheckedChange={() => toggleContact(c.id)}
                      />
                      <div
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${getAvatarColor(c.type)}`}
                      >
                        {getInitials(c.name)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-foreground truncate">
                          {c.name}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {c.email}
                        </p>
                      </div>
                    </label>
                  ))}
                  {filteredContacts.length === 0 && (
                    <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                      {search ? "No contacts match your search." : "All contacts selected."}
                    </p>
                  )}
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t p-4 mt-auto">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!name.trim()}
            className="bg-[#6366F1] text-white hover:bg-[#4F46E5]"
          >
            {isEditing
              ? "Save Changes"
              : `Create Group${selectedIds.length > 0 ? ` (${selectedIds.length} members)` : ""}`}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
