import React, { useState } from 'react';
import { Database, Table, Key, Link2, ChevronRight, ChevronDown, Search, RotateCw } from 'lucide-react';

export default function SchemaExplorer({
  schema,
  loading,
  error,
  onRefresh,
  activeConnectorName,
  databaseType,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedTables, setExpandedTables] = useState({});

  const toggleTable = (tableName) => {
    setExpandedTables((prev) => ({
      ...prev,
      [tableName]: !prev[tableName],
    }));
  };

  const tables = schema?.tables || [];
  const filteredTables = tables.filter((t) =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <aside className="clay-panel" style={{ padding: '1.5rem', height: 'fit-content' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            background: 'var(--clay-btn-secondary-bg)',
            boxShadow: 'var(--clay-btn-secondary-shadow)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Database size={15} color="var(--accent-primary)" />
          </div>
          <h2 style={{ fontSize: '0.98rem', fontWeight: '800', letterSpacing: '-0.01em' }}>Schema Explorer</h2>
        </div>
        <button
          className="clay-icon-btn"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh schema"
          aria-label="Refresh schema"
        >
          <RotateCw
            size={15}
            className={`refresh-icon ${loading ? 'animate-spin' : ''}`}
            color="var(--accent-primary)"
          />
        </button>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <div className="clay-carved" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.5rem 0.85rem',
        }}>
          <Search size={14} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Filter tables..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.82rem',
              width: '100%',
            }}
          />
        </div>
      </div>

      {error ? (
        <div className="clay-carved" style={{
          background: 'rgba(244, 63, 94, 0.08)',
          border: '1px solid rgba(244, 63, 94, 0.25)',
          borderRadius: 'var(--radius-md)',
          padding: '0.95rem',
          fontSize: '0.78rem',
          color: 'var(--text-primary)',
          lineHeight: '1.45',
        }}>
          <div style={{ fontWeight: 700, color: '#f43f5e', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span>Connection / Auth Failed</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
            {error}
          </p>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.45rem' }}>
            Tip: Edit credentials in your <code style={{ color: '#38bdf8' }}>.env</code> file.
          </div>
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--clay-btn-secondary-bg)',
            boxShadow: 'var(--clay-btn-secondary-shadow)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 0.75rem',
          }}>
            <RotateCw size={19} className="animate-spin" color="var(--accent-primary)" />
          </div>
          Discovering schema catalog...
        </div>
      ) : filteredTables.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '1.8rem 1rem', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No tables found in catalog.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem', maxHeight: '650px', overflowY: 'auto', paddingRight: '0.2rem' }}>
          {filteredTables.map((table) => {
            const isExpanded = !!expandedTables[table.name];
            return (
              <div
                key={table.name}
                style={{
                  background: isExpanded ? 'var(--clay-panel-bg)' : 'var(--clay-btn-secondary-bg)',
                  boxShadow: isExpanded ? 'var(--clay-carved-shadow)' : 'var(--clay-btn-secondary-shadow)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                  transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
                }}
              >
                <div
                  onClick={() => toggleTable(table.name)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    cursor: 'pointer',
                    userSelect: 'none',
                    fontSize: '0.83rem',
                    fontWeight: 700,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                    {isExpanded ? <ChevronDown size={14} color="var(--accent-primary)" /> : <ChevronRight size={14} color="var(--text-muted)" />}
                    <Table size={13} color="var(--text-secondary)" />
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{table.name}</span>
                  </div>
                  <span className="clay-pill" style={{
                    fontSize: '0.68rem',
                    color: 'var(--text-secondary)',
                    background: 'var(--hover-overlay)',
                    padding: '0.15rem 0.45rem',
                    border: '1px solid var(--border-subtle)',
                  }}>
                    {table.columns.length} cols
                  </span>
                </div>

                {isExpanded && (
                  <div style={{ padding: '0.5rem 0.85rem 0.75rem', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-input)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      {table.columns.map((col) => (
                        <div
                          key={col.name}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            fontSize: '0.75rem',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            {col.is_primary_key && <Key size={11} color="#f59e0b" title="Primary Key" />}
                            {col.foreign_key && <Link2 size={11} color="#06b6d4" title={`Foreign Key -> ${col.foreign_key}`} />}
                            <span style={{ color: col.is_primary_key ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                              {col.name}
                            </span>
                          </div>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                            {col.data_type}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </aside>
  );
}
