"use client";

import React from "react"

import { useCallback, useState } from "react";
import { Upload, FileText, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ContactType, Group } from "./data";

interface ParsedRow {
  name: string;
  email: string;
  phone: string;
  status: "valid" | "error" | "duplicate";
  reason?: string;
}

interface ImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groups: Group[];
  existingEmails: string[];
  onImport: (
    rows: { name: string; email: string; phone: string }[],
    type: ContactType,
    groupId: string | null
  ) => void;
}

export function ImportModal({
  open,
  onOpenChange,
  groups,
  existingEmails,
  onImport,
}: ImportModalProps) {
  const [step, setStep] = useState<"input" | "preview">("input");
  const [csvText, setCsvText] = useState(
    "name, email, phone\nSarah Chen, sarah@acme.com, 3105550142\nJohn Doe, john@doe.com,"
  );
  const [contactType, setContactType] = useState<ContactType>("client");
  const [groupId, setGroupId] = useState<string | null>(null);
  const [parsed, setParsed] = useState<ParsedRow[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const resetState = useCallback(() => {
    setStep("input");
    setCsvText(
      "name, email, phone\nSarah Chen, sarah@acme.com, 3105550142\nJohn Doe, john@doe.com,"
    );
    setContactType("client");
    setGroupId(null);
    setParsed([]);
  }, []);

  const handleOpenChange = (val: boolean) => {
    if (!val) resetState();
    onOpenChange(val);
  };

  const parseCSV = () => {
    const lines = csvText
      .trim()
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (lines.length < 2) return;

    const rows: ParsedRow[] = [];
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c) => c.trim());
      const name = cols[0] || "";
      const email = cols[1] || "";
      const phone = cols[2] || "";

      if (!name || !email || !email.includes("@")) {
        rows.push({ name, email, phone, status: "error", reason: "Missing name or invalid email" });
      } else if (existingEmails.includes(email.toLowerCase())) {
        rows.push({ name, email, phone, status: "duplicate", reason: "Already exists" });
      } else {
        rows.push({ name, email, phone, status: "valid" });
      }
    }
    setParsed(rows);
    setStep("preview");
  };

  const validRows = parsed.filter((r) => r.status === "valid");
  const errorCount = parsed.filter((r) => r.status === "error").length;
  const dupeCount = parsed.filter((r) => r.status === "duplicate").length;

  const handleImport = () => {
    onImport(
      validRows.map((r) => ({ name: r.name, email: r.email, phone: r.phone })),
      contactType,
      groupId
    );
    handleOpenChange(false);
  };

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          setCsvText((ev.target?.result as string) || "");
        };
        reader.readAsText(file);
      }
    },
    []
  );

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[520px] gap-0 p-0 overflow-hidden">
        <DialogHeader className="p-6 pb-4">
          <DialogTitle>Import Contacts</DialogTitle>
          <DialogDescription>
            Upload a CSV file or paste data to bulk-import contacts.
          </DialogDescription>
        </DialogHeader>

        {step === "input" && (
          <>
            <div className="px-6 space-y-4">
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
                className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
                  dragOver ? "border-[#6366F1] bg-[#EEF2FF]" : "border-border"
                }`}
              >
                <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm font-medium text-foreground">
                  Drag & drop your CSV file here
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Supports .csv and .xlsx files
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Separator className="flex-1" />
                <span className="text-xs text-muted-foreground">or paste manually</span>
                <Separator className="flex-1" />
              </div>

              <Textarea
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                placeholder={"name, email, phone\nJane Doe, jane@example.com, 5551234567"}
                className="min-h-[120px] font-mono text-xs"
              />

              <Separator />

              <div className="grid grid-cols-2 gap-3 pb-2">
                <div>
                  <Label className="text-sm font-medium">Assign to group</Label>
                  <Select
                    value={groupId ?? "none"}
                    onValueChange={(v) => setGroupId(v === "none" ? null : v)}
                  >
                    <SelectTrigger className="mt-1.5">
                      <SelectValue placeholder="Select a group (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {groups.map((g) => (
                        <SelectItem key={g.id} value={g.id}>
                          {g.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Contact type</Label>
                  <Select
                    value={contactType}
                    onValueChange={(v) => setContactType(v as ContactType)}
                  >
                    <SelectTrigger className="mt-1.5">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="client">Client</SelectItem>
                      <SelectItem value="agent">Agent</SelectItem>
                      <SelectItem value="list">List</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 border-t p-4">
              <Button variant="outline" onClick={() => handleOpenChange(false)}>
                Cancel
              </Button>
              <Button
                onClick={parseCSV}
                className="bg-[#6366F1] text-white hover:bg-[#4F46E5]"
              >
                Preview Import
              </Button>
            </div>
          </>
        )}

        {step === "preview" && (
          <>
            <div className="px-6 space-y-3">
              <p className="text-sm font-medium text-foreground">
                Preview ({parsed.length} contacts found)
              </p>
              <ScrollArea className="h-[220px] rounded-lg border">
                <div className="divide-y">
                  {parsed.map((row, i) => (
                    <div
                      key={`${row.email}-${i}`}
                      className="flex items-center gap-3 px-3 py-2.5"
                    >
                      {row.status === "valid" && (
                        <CheckCircle2 className="h-4 w-4 shrink-0 text-[#6366F1]" />
                      )}
                      {row.status === "error" && (
                        <XCircle className="h-4 w-4 shrink-0 text-destructive" />
                      )}
                      {row.status === "duplicate" && (
                        <AlertTriangle className="h-4 w-4 shrink-0 text-[#94A3B8]" />
                      )}
                      <span className="text-sm text-foreground truncate min-w-0 flex-1">
                        {row.name || "—"}
                      </span>
                      <span className="text-xs text-muted-foreground truncate max-w-[160px]">
                        {row.email || "—"}
                      </span>
                      <span
                        className={`text-xs font-medium shrink-0 ${
                          row.status === "valid"
                            ? "text-[#4338CA]"
                            : row.status === "error"
                              ? "text-destructive"
                              : "text-muted-foreground"
                        }`}
                      >
                        {row.status === "valid"
                          ? "valid"
                          : row.status === "error"
                            ? "error"
                            : "exists"}
                      </span>
                    </div>
                  ))}
                </div>
              </ScrollArea>
              <p className="text-xs text-muted-foreground pb-1">
                {validRows.length} valid
                {errorCount > 0 && ` · ${errorCount} error${errorCount > 1 ? "s" : ""}`}
                {dupeCount > 0 && ` · ${dupeCount} duplicate${dupeCount > 1 ? "s" : ""} (will skip)`}
              </p>
            </div>

            <div className="flex items-center justify-end gap-2 border-t p-4">
              <Button variant="outline" onClick={() => setStep("input")}>
                Back
              </Button>
              <Button
                onClick={handleImport}
                disabled={validRows.length === 0}
                className="bg-[#6366F1] text-white hover:bg-[#4F46E5]"
              >
                Import {validRows.length} Contact{validRows.length !== 1 ? "s" : ""}
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
