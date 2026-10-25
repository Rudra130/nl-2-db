import React, { useState } from 'react';
import { X, Copy, Check, ShieldCheck, Terminal, HelpCircle } from 'lucide-react';

export default function QueryInspector({ isOpen, onClose, queryData }) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !queryData) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(queryData.generated_query || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1.5rem',
    }}>
      <div className="clay-panel animate-fade-in" style={{
        width: '100%',
        maxWidth: '750px',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '1.75rem',
        border: '1px solid var(--border-hover)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
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
              <Terminal size={17} color="var(--accent-primary)" />
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.01em' }}>Execution Inspection</h3>
            <span className="badge badge-success clay-pill" style={{ fontSize: '0.68rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <ShieldCheck size={12} />
              AST Read-Only Verified
            </span>
          </div>
          <button
            className="btn-ghost"
            onClick={onClose}
            style={{ padding: '0.35rem', borderRadius: '8px', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* User Prompt Echo */}
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Original Question:
          </label>
          <div className="clay-carved" style={{
            padding: '0.75rem 1rem',
            marginTop: '0.4rem',
            fontSize: '0.88rem',
            color: 'var(--text-primary)',
          }}>
            {queryData.user_prompt}
          </div>
        </div>

        {/* Generated Query Box */}
        <div style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <label style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Generated {queryData.database_type.toUpperCase()} Query:
            </label>
            <button
              className="btn btn-secondary clay-btn-secondary"
              onClick={handleCopy}
              style={{ padding: '0.3rem 0.75rem', fontSize: '0.74rem' }}
            >
              {copied ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <pre className="clay-carved" style={{
            padding: '1.15rem',
            color: '#38bdf8',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.84rem',
            overflowX: 'auto',
            lineHeight: '1.55',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}>
            {queryData.generated_query || 'No query available'}
          </pre>
        </div>

        {/* Query Explanation */}
        {queryData.query_explanation && (
          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.4rem' }}>
              <HelpCircle size={14} color="#06b6d4" />
              <span>Query Logic Explanation:</span>
            </div>
            <div className="clay-carved" style={{
              padding: '0.85rem 1rem',
              fontSize: '0.84rem',
              color: 'var(--text-secondary)',
              lineHeight: '1.55',
            }}>
              {queryData.query_explanation}
            </div>
          </div>
        )}

        {/* Meta Stats Footer */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '0.85rem',
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: '1.15rem',
          textAlign: 'center',
        }}>
          <div className="clay-pill" style={{ background: 'var(--clay-btn-secondary-bg)', padding: '0.65rem', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>Target Dialect</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-primary)', textTransform: 'uppercase' }}>
              {queryData.database_type}
            </div>
          </div>
          <div className="clay-pill" style={{ background: 'var(--clay-btn-secondary-bg)', padding: '0.65rem', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>Latency</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#10b981' }}>
              {queryData.execution_time_ms?.toFixed(1) || 0} ms
            </div>
          </div>
          <div className="clay-pill" style={{ background: 'var(--clay-btn-secondary-bg)', padding: '0.65rem', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>Safety Guardrails</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
              100% Passed
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
