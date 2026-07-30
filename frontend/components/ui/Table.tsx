'use client';

import React from 'react';
import { ChevronUp, ChevronDown, Inbox } from 'lucide-react';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  className?: string;
  render?: (row: T, index: number) => React.ReactNode;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  sortKey?: string;
  sortDir?: 'asc' | 'desc';
  onSort?: (key: string) => void;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  onRowClick?: (row: T) => void;
  rowKey?: (row: T) => string | number;
  className?: string;
}

export default function Table<T extends Record<string, unknown>>({
  columns,
  data,
  sortKey,
  sortDir = 'asc',
  onSort,
  emptyMessage = 'No data found',
  emptyIcon,
  onRowClick,
  rowKey,
  className = '',
}: TableProps<T>) {
  if (data.length === 0) {
    return (
      <div className={`glass rounded-2xl p-12 text-center ${className}`}>
        {emptyIcon || <Inbox className="w-12 h-12 text-[var(--color-text-muted)]/30 mx-auto mb-4" />}
        <p className="text-sm text-[var(--color-text-muted)]">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`glass rounded-2xl overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`
                    px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider
                    text-[var(--color-text-muted)]
                    ${col.sortable ? 'cursor-pointer hover:text-[var(--color-text)] select-none' : ''}
                    ${col.className || ''}
                  `}
                  onClick={col.sortable && onSort ? () => onSort(col.key) : undefined}
                >
                  <span className="flex items-center gap-1">
                    {col.header}
                    {col.sortable && sortKey === col.key && (
                      sortDir === 'asc'
                        ? <ChevronUp className="w-3 h-3" />
                        : <ChevronDown className="w-3 h-3" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr
                key={rowKey ? rowKey(row) : i}
                className={`
                  border-b border-[var(--color-border)] last:border-0
                  transition-colors duration-150
                  ${onRowClick ? 'cursor-pointer hover:bg-white/[0.04]' : ''}
                `}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((col) => (
                  <td key={col.key} className={`px-4 py-3 text-sm text-[var(--color-text)] ${col.className || ''}`}>
                    {col.render
                      ? col.render(row, i)
                      : (row[col.key] as React.ReactNode) ?? '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
