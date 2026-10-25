import React from 'react';
import { AlertTriangle, ShieldAlert, X } from 'lucide-react';

export default function ErrorBanner({ error, status, onClose }) {
  if (!error) return null;

  const isRejection = status === 'rejected';

  return (
    <div className="clay-panel animate-fade-in" style={{
      padding: '1.15rem 1.35rem',
      marginBottom: '1.75rem',
      background: isRejection ? 'rgba(244, 63, 94, 0.10)' : 'rgba(245, 158, 11, 0.10)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      border: `1px solid ${isRejection ? 'rgba(244, 63, 94, 0.35)' : 'rgba(245, 158, 11, 0.35)'}`,
      boxShadow: `var(--clay-panel-shadow), 0 0 20px ${isRejection ? 'rgba(244, 63, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)'}`,
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: '1rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
        <div style={{
          padding: '0.5rem',
          borderRadius: '12px',
          background: isRejection ? 'rgba(244, 63, 94, 0.18)' : 'rgba(245, 158, 11, 0.18)',
          boxShadow: isRejection
            ? '0 4px 10px rgba(244, 63, 94, 0.3), inset 2px 2px 4px rgba(255, 255, 255, 0.3), inset -2px -2px 4px rgba(0, 0, 0, 0.3)'
            : '0 4px 10px rgba(245, 158, 11, 0.3), inset 2px 2px 4px rgba(255, 255, 255, 0.3), inset -2px -2px 4px rgba(0, 0, 0, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          {isRejection ? <ShieldAlert size={19} color="#f43f5e" /> : <AlertTriangle size={19} color="#f59e0b" />}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem', marginBottom: '0.3rem' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 800, color: isRejection ? '#f43f5e' : '#f59e0b', letterSpacing: '-0.01em' }}>
              {isRejection ? 'Security Policy Blocked Request' : 'Execution Notice'}
            </h4>
            <span className={`badge ${isRejection ? 'badge-danger' : 'badge-warning'} clay-pill`} style={{ fontSize: '0.68rem' }}>
              {status}
            </span>
          </div>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-primary)', lineHeight: 1.55 }}>
            {error}
          </p>
        </div>
      </div>

      {onClose && (
        <button
          className="btn-ghost"
          onClick={onClose}
          style={{ padding: '0.25rem', borderRadius: '4px', cursor: 'pointer', flexShrink: 0 }}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}
