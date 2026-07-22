import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DataTable } from './DataTable'

interface Row {
  id: string
  name: string
}

describe('DataTable', () => {
  it('renders the empty message when there are no rows', () => {
    render(
      <DataTable<Row>
        columns={[{ key: 'name', header: 'Name', render: (row) => row.name }]}
        rows={[]}
        getRowKey={(row) => row.id}
        emptyMessage="Nothing here."
      />,
    )

    expect(screen.getByText('Nothing here.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('renders one row per item, using each column render function', () => {
    render(
      <DataTable<Row>
        columns={[{ key: 'name', header: 'Name', render: (row) => row.name }]}
        rows={[
          { id: '1', name: 'Alpha' },
          { id: '2', name: 'Beta' },
        ]}
        getRowKey={(row) => row.id}
        emptyMessage="Nothing here."
      />,
    )

    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('Alpha')).toBeInTheDocument()
    expect(screen.getByText('Beta')).toBeInTheDocument()
  })
})
