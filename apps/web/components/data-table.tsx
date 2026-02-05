"use client"

import type React from "react"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface Column<T> {
  key: keyof T
  label: string
  render?: (value: T[keyof T], row: T) => React.ReactNode
  className?: string
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  className?: string
  searchable?: boolean
  searchPlaceholder?: string
  onSearch?: (query: string) => void
  toolbar?: React.ReactNode
  emptyMessage?: string
  footer?: React.ReactNode
  onRowClick?: (row: T) => void
}

export function DataTable<T extends Record<string, any>>({ 
  data, 
  columns, 
  className,
  searchable = false,
  searchPlaceholder = "Search...",
  onSearch,
  toolbar,
  emptyMessage = "No data available",
  footer,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div className={cn("bg-card border border-border rounded-xl overflow-hidden shadow-sm", className)}>
      {/* Table toolbar */}
      {(searchable || toolbar) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            {searchable && (
              <Input
                placeholder={searchPlaceholder}
                className="w-64 h-8 text-sm"
                onChange={(e) => onSearch?.(e.target.value)}
              />
            )}
            {toolbar}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {data.length} {data.length === 1 ? 'result' : 'results'}
          </div>
        </div>
      )}

      {/* Table */}
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            {columns.map((column) => (
              <TableHead 
                key={String(column.key)} 
                className="text-xs font-medium text-muted-foreground uppercase tracking-wider"
              >
                {column.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="text-center py-8 text-muted-foreground">
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            data.map((row, rowIndex) => (
              <TableRow 
                key={rowIndex} 
                className={cn(
                  "hover:bg-muted/30 transition-colors",
                  onRowClick && "cursor-pointer"
                )}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((column) => (
                  <TableCell key={String(column.key)} className={cn("text-sm py-3", column.className)}>
                    {column.render ? column.render(row[column.key], row) : String(row[column.key] ?? '')}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {/* Pagination footer */}
      {footer && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-border">
          {footer}
        </div>
      )}
    </div>
  )
}
