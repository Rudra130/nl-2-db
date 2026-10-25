import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Download, Search, Table as TableIcon } from 'lucide-react';

export default function ResultTable({ columns, rows, executionTimeMs }) {
  const [filterText, setFilterText] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const handleSort = (col) => {
    let direction = 'asc';
    if (sortConfig.key === col && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key: col, direction });
  };

  const filteredRows = useMemo(() => {
    if (!filterText.trim()) return rows;
    const lower = filterText.toLowerCase();
    return rows.filter((row) =>
      Object.values(row).some((val) =>
        String(val ?? '').toLowerCase().includes(lower)
      )
    );
  }, [rows, filterText]);

  const sortedRows = useMemo(() => {
    if (!sortConfig.key) return filteredRows;
    return [...filteredRows].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }
      return sortConfig.direction === 'asc'
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });
  }, [filteredRows, sortConfig]);

  const totalPages = Math.ceil(sortedRows.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [sortedRows, currentPage, pageSize]);

  const downloadCSV = () => {
    if (!rows.length || !columns.length) return;
    const headers = columns.join(',');
    const csvLines = rows.map((r) =>
      columns.map((c) => {
        const val = r[c] ?? '';
        return `"${String(val).replace(/"/g, '""')}"`;
      }).join(',')
    );
    const blob = new Blob([[headers, ...csvLines].join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nl2db_export_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!columns.length && !rows.length) {
    return (
      <div className="clay-panel" style={{ padding: '4rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{
          width: '54px',
          height: '54px',
          borderRadius: '16px',
          background: 'var(--clay-btn-secondary-bg)',
          boxShadow: 'var(--clay-btn-secondary-shadow)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1.25rem',
        }}>
          <TableIcon size={28} color="var(--accent-primary)" />
        </div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.4rem', letterSpacing: '-0.01em' }}>
          No Query Executed Yet
        </h3>
        <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', maxWidth: '420px', margin: '0 auto' }}>
          Ask a question above or pick one of the sample prompt pills to retrieve and analyze live database records.
        </p>
      </div>
    );
  }

  return (
    <div className="clay-panel" style={{ padding: '1.5rem' }}>
      {/* Controls Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '10px',
            background: 'var(--clay-btn-secondary-bg)',
            boxShadow: 'var(--clay-btn-secondary-shadow)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <TableIcon size={16} color="var(--accent-cyan)" />
          </div>
          <div>
            <h3 style={{ fontSize: '0.98rem', fontWeight: 800, letterSpacing: '-0.01em' }}>
              Query Results
            </h3>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Showing {sortedRows.length} {sortedRows.length === 1 ? 'row' : 'rows'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          {/* Quick Filter */}
          <div className="clay-carved" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.45rem 0.8rem',
          }}>
            <Search size={13} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search in rows..."
              value={filterText}
              onChange={(e) => {
                setFilterText(e.target.value);
                setCurrentPage(1);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
                width: '140px',
              }}
            />
          </div>

          {/* Export CSV */}
          <button
            className="btn btn-secondary clay-btn-secondary"
            onClick={downloadCSV}
            style={{ padding: '0.45rem 0.95rem', fontSize: '0.8rem' }}
            title="Download CSV"
          >
            <Download size={13} />
            Export CSV
          </button>
        </div>
      </div>

      {/* Tabular View */}
      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => {
                const isSorted = sortConfig.key === col;
                return (
                  <th
                    key={col}
                    onClick={() => handleSort(col)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <span>{col}</span>
                      {isSorted ? (
                        sortConfig.direction === 'asc' ? <ArrowUp size={13} color="#8b5cf6" /> : <ArrowDown size={13} color="#8b5cf6" />
                      ) : (
                        <ArrowUpDown size={12} color="var(--text-disabled)" />
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No records match your filter criteria.
                </td>
              </tr>
            ) : (
              paginatedRows.map((row, rIdx) => (
                <tr key={rIdx}>
                  {columns.map((col) => {
                    const val = row[col];
                    const displayVal = val === null || val === undefined ? (
                      <span style={{ color: 'var(--text-disabled)', fontStyle: 'italic' }}>NULL</span>
                    ) : typeof val === 'object' ? (
                      JSON.stringify(val)
                    ) : (
                      String(val)
                    );
                    return <td key={col}>{displayVal}</td>;
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className="btn btn-secondary clay-btn-secondary"
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
            >
              Previous
            </button>
            <button
              className="btn btn-secondary clay-btn-secondary"
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
