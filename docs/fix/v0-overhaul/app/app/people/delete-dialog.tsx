"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface DeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contactNames: string[];
  onConfirm: () => void;
}

export function DeleteDialog({
  open,
  onOpenChange,
  contactNames,
  onConfirm,
}: DeleteDialogProps) {
  const count = contactNames.length;
  const isBulk = count > 1;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {isBulk ? `Delete ${count} Contacts?` : "Delete Contact?"}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {isBulk ? (
              <>
                These contacts will be permanently removed from your contacts
                and all groups. This cannot be undone.
              </>
            ) : (
              <>
                &ldquo;{contactNames[0]}&rdquo; will be permanently removed
                from your contacts and all groups. This cannot be undone.
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isBulk ? `Delete ${count} Contacts` : "Delete Contact"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
