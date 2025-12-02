"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { MoreHorizontal, Power, PowerOff, Loader2 } from "lucide-react"

interface AffiliateActionsProps {
  affiliate: {
    account_id: string
    name: string
    is_active: boolean
  }
}

export function AffiliateActions({ affiliate }: AffiliateActionsProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  async function toggleStatus() {
    setLoading(true)
    try {
      const res = await fetch(`/api/proxy/v1/admin/affiliates/${affiliate.account_id}?is_active=${!affiliate.is_active}`, {
        method: "PATCH",
      })

      if (!res.ok) {
        throw new Error("Failed to update affiliate")
      }

      router.refresh()
    } catch (error) {
      console.error("Failed to update affiliate:", error)
    } finally {
      setLoading(false)
      setShowConfirm(false)
    }
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" disabled={loading}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Actions
                <MoreHorizontal className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={() => setShowConfirm(true)}
            className={affiliate.is_active ? "text-red-600" : "text-green-600"}
          >
            {affiliate.is_active ? (
              <>
                <PowerOff className="h-4 w-4 mr-2" />
                Deactivate
              </>
            ) : (
              <>
                <Power className="h-4 w-4 mr-2" />
                Activate
              </>
            )}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {affiliate.is_active ? "Deactivate" : "Activate"} {affiliate.name}?
            </AlertDialogTitle>
            <AlertDialogDescription>
              {affiliate.is_active
                ? "This will disable the affiliate account and all their sponsored agents will no longer be able to generate reports."
                : "This will re-enable the affiliate account and their sponsored agents."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={toggleStatus}
              className={affiliate.is_active ? "bg-red-600 hover:bg-red-700" : ""}
            >
              {affiliate.is_active ? "Deactivate" : "Activate"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
