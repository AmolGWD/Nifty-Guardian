import type { ReactNode } from 'react'
import styles from './DataTable.module.css'
import { EmptyState } from './EmptyState'

export interface DataTableColumn<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  align?: 'left' | 'right'
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  rows: T[]
  getRowKey: (row: T) => string
  emptyMessage: string
}

/** A generic, column-defined table - used by Orders/Positions; renders EmptyState when rows is empty. */
export function DataTable<T>({ columns, rows, getRowKey, emptyMessage }: DataTableProps<T>) {
  if (rows.length === 0) {
    return <EmptyState message={emptyMessage} />
  }

  return (
    <table className={styles.table}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th
              key={column.key}
              className={column.align === 'right' ? styles.alignRight : undefined}
            >
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={getRowKey(row)}>
            {columns.map((column) => (
              <td
                key={column.key}
                className={column.align === 'right' ? styles.alignRight : undefined}
              >
                {column.render(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
