import React from 'react';
import { Database, CheckCircle2, XCircle, RotateCw, Activity, Terminal, Sun, Moon } from 'lucide-react';

export default function Header({
  connections,
  activeConnectorId,
  onSelectConnector,
  onTestConnection,
  testingConnection,
  health,
  onOpenInspector,
  hasQuery,
  theme,
  onToggleTheme,
}) {
  const activeConn = connections.find((c) => c.id === activeConnectorId);

  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(20px)',
      position: 'sticky',
      top: 0,
      zIndex: 40,
      padding: '0.9rem 2rem',
      borderRadius: '0 0 var(--radius-xl) var(--radius-xl)',
      boxShadow: '0 12px 30px -8px rgba(0, 0, 0, 0.25), inset 0 2px 4px rgba(255, 255, 255, 0.05)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '1rem',
      transition: 'var(--transition)',
    }}>
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '14px',
          background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 8px 20px -3px rgba(124, 58, 237, 0.45), inset 3px 3px 6px rgba(255, 255, 255, 0.5), inset -3px -3px 6px rgba(0, 0, 0, 0.4)',
        }}>
          <Database size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <h1 style={{
              fontSize: '1.25rem',
              fontWeight: '800',
              letterSpacing: '-0.02em',
              background: 'linear-gradient(to right, var(--text-primary), var(--text-secondary))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              NL2DB Platform
            </h1>
            <span className="badge badge-success clay-pill" style={{ fontSize: '0.7rem' }}>
              v1.0 Read-Only AST
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Natural Language AI Agent to Multi-Database Query Engine
          </p>
        </div>
      </div>

      {/* Connection Switcher, Theme Switcher & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        {/* Connector Selector */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          background: 'var(--clay-btn-secondary-bg)',
          boxShadow: 'var(--clay-btn-secondary-shadow)',
          padding: '0.4rem 0.75rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            Target DB:
          </span>
          <select
            value={activeConnectorId}
            onChange={(e) => onSelectConnector(e.target.value)}
            style={{
              background: 'transparent',
              color: 'var(--text-primary)',
              border: 'none',
              outline: 'none',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            {connections.map((conn) => (
              <option
                key={conn.id}
                value={conn.id}
                style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              >
                {conn.name} ({conn.database_type.toUpperCase()})
              </option>
            ))}
          </select>

          {activeConn && (
            <span
              className={`badge badge-${activeConn.database_type} clay-pill`}
              style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}
            >
              {activeConn.database_type}
            </span>
          )}
        </div>

        {/* Test Connection Button */}
        <button
          className="btn btn-secondary clay-btn-secondary"
          onClick={onTestConnection}
          disabled={testingConnection}
          style={{ padding: '0.48rem 0.95rem', fontSize: '0.8rem' }}
          title="Verify database connectivity"
        >
          <RotateCw size={14} className={`refresh-icon ${testingConnection ? 'animate-spin' : ''}`} color="var(--accent-primary)" />
          {testingConnection ? 'Testing...' : 'Ping DB'}
        </button>

        {/* Query Inspector Drawer Trigger */}
        {hasQuery && (
          <button
            className="btn btn-secondary"
            onClick={onOpenInspector}
            style={{ padding: '0.48rem 0.95rem', fontSize: '0.8rem' }}
          >
            <Terminal size={14} color="var(--accent-primary)" />
            Inspect Query
          </button>
        )}

        {/* Health status pill */}
        <div className="clay-pill" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          background: 'var(--clay-btn-secondary-bg)',
          boxShadow: 'var(--clay-btn-secondary-shadow)',
          padding: '0.45rem 0.85rem',
          borderRadius: 'var(--radius-full)',
          fontSize: '0.75rem',
          border: '1px solid var(--border-subtle)',
        }}>
          <span
            className="pulse-indicator"
            style={{
              background: health?.status === 'healthy' ? 'var(--accent-emerald)' : 'var(--accent-amber)',
              boxShadow: `0 0 10px ${health?.status === 'healthy' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}`,
            }}
          />
          <span style={{ color: 'var(--text-secondary)' }}>
            LLM: <strong style={{ color: 'var(--text-primary)' }}>{health?.llm_mode || 'ready'}</strong>
          </span>
        </div>

        {/* Dark / Light Mode Toggle Button */}
        <button
          className="btn btn-secondary"
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          style={{
            padding: '0.42rem 0.75rem',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            borderRadius: 'var(--radius-md)',
          }}
        >
          {theme === 'dark' ? (
            <>
              <Sun size={15} color="#f59e0b" />
              <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>Light</span>
            </>
          ) : (
            <>
              <Moon size={15} color="var(--accent-primary)" />
              <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>Dark</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
