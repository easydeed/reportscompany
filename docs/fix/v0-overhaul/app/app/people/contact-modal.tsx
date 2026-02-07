"use client";

import { useEffect, useState } from "react";
import { Search, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { Contact, ContactType, Group } from "./data";
import { getInitials, getAvatarColor } from "./data";

interface ContactModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contact: Contact | null;
  groups: Group[];
  onSave: (data: {
    name: string;
    email: string;
    phone: string;
    type: ContactType;
    groupIds: string[];
  }) => void;
}

export function ContactModal({
  open,
  onOpenChange,
  contact,
  groups,
  onSave,
}: ContactModalProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [type, setType] = useState<ContactType>("client");
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [groupSearch, setGroupSearch] = useState("");

  useEffect(() => {
    if (open) {
      if (contact) {
        setName(contact.name);
        setEmail(contact.email);
        setPhone(contact.phone);
        setType(contact.type);
        setSelectedGroups(contact.groupIds);
      } else {
        setName("");
        setEmail("");
        setPhone("");
        setType("client");
        setSelectedGroups([]);
      }
      setGroupSearch("");
    }
  }, [open, contact]);

  const filteredGroups = groups.filter((g) =>
    g.name.toLowerCase().includes(groupSearch.toLowerCase())
  );

  const toggleGroup = (gid: string) => {
    setSelectedGroups((prev) =>
      prev.includes(gid) ? prev.filter((id) => id !== gid) : [...prev, gid]
    );
  };

  const handleSubmit = () => {
    if (!name.trim() || !email.trim()) return;
    onSave({ name: name.trim(), email: email.trim(), phone: phone.trim(), type, groupIds: selectedGroups });
  };

  const isEditing = !!contact;

  const typeOptions: { value: ContactType; label: string; desc: string }[] = [
    { value: "client", label: "Client", desc: "Primary contacts" },
    { value: "agent", label: "Agent", desc: "Industry partners" },
    { value: "list", label: "List", desc: "Mailing list" },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px] gap-0 p-0 overflow-hidden">
        <DialogHeader className="p-6 pb-4">
          <DialogTitle>{isEditing ? "Edit Contact" : "Add Contact"}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update contact information and group assignments."
              : "Add a new contact to your database."}
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 pb-2 space-y-4">
          <div>
            <Label htmlFor="contact-name" className="text-sm font-medium">
              Full Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="contact-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Sarah Chen"
              className="mt-1.5"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="contact-email" className="text-sm font-medium">
                Email <span className="text-destructive">*</span>
              </Label>
              <Input
                id="contact-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@example.com"
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="contact-phone" className="text-sm font-medium">
                Phone
              </Label>
              <Input
                id="contact-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="(555) 123-4567"
                className="mt-1.5"
              />
            </div>
          </div>

          <div>
            <Label className="text-sm font-medium">Contact Type</Label>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {typeOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setType(opt.value)}
                  className={`rounded-lg border p-3 text-left transition-all ${
                    type === opt.value
                      ? "border-[#6366F1] bg-[#EEF2FF] ring-1 ring-[#6366F1]"
                      : "border-border hover:border-[#C7D2FE]"
                  }`}
                >
                  <p className="text-sm font-medium text-foreground">
                    {opt.label}
                  </p>
                  <p className="text-xs text-muted-foreground">{opt.desc}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <Separator className="my-2" />

        <div className="px-6 pb-2">
          <Label className="text-sm font-medium">
            Add to Groups{" "}
            <span className="text-muted-foreground font-normal">(optional)</span>
          </Label>
          <div className="mt-2 relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={groupSearch}
              onChange={(e) => setGroupSearch(e.target.value)}
              placeholder="Search or create a group..."
              className="pl-9"
            />
          </div>
          <ScrollArea className="mt-2 h-[140px] rounded-md border">
            <div className="p-2 space-y-1">
              {filteredGroups.map((g) => (
                <label
                  key={g.id}
                  className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-muted cursor-pointer"
                >
                  <Checkbox
                    checked={selectedGroups.includes(g.id)}
                    onCheckedChange={() => toggleGroup(g.id)}
                  />
                  <span className="text-sm text-foreground">{g.name}</span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {g.memberIds.length}
                  </span>
                </label>
              ))}
              {filteredGroups.length === 0 && groupSearch.trim() && (
                <p className="px-2 py-2 text-sm text-muted-foreground">
                  No groups found
                </p>
              )}
            </div>
          </ScrollArea>
          {selectedGroups.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {selectedGroups.map((gid) => {
                const g = groups.find((gr) => gr.id === gid);
                if (!g) return null;
                return (
                  <span
                    key={gid}
                    className="inline-flex items-center gap-1 rounded-full bg-[#EEF2FF] px-2.5 py-1 text-xs font-medium text-[#4338CA]"
                  >
                    {g.name}
                    <button
                      type="button"
                      onClick={() => toggleGroup(gid)}
                      className="ml-0.5 rounded-full hover:bg-[#C7D2FE] p-0.5"
                    >
                      <X className="h-3 w-3" />
                      <span className="sr-only">Remove {g.name}</span>
                    </button>
                  </span>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 border-t p-4">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!name.trim() || !email.trim()}
            className="bg-[#6366F1] text-white hover:bg-[#4F46E5]"
          >
            {isEditing ? "Save Changes" : "Save Contact"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
