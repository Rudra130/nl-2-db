import React from 'react';
import { Sparkles, TrendingUp, Clock, ListOrdered, CheckCircle2 } from 'lucide-react';

export default function SummaryCard({
  summary,
  insights,
  rowCount,
  executionTimeMs,
  retryCount,
}) {
  if (!summary) return null;

  return (
    <div className="clay-panel animate-fade-in" style={{
      padding: '1.5rem',
      marginBottom: '1.75rem',
      background: 'var(--summary-card-bg)',
      border: '1px solid var(--border-hover)',
      boxShadow: 'var(--clay-panel-shadow), 0 0 24px var(--accent-purple-glow)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.9rem', flexWrap: 'wrap', gap: '0.6rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
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
            <Sparkles size={17} color="var(--accent-primary)" />
          </div>
          <h3 style={{ fontSize: '1rem', fontWeight: '800', letterSpacing: '-0.01em', color: 'var(--text-primary)' }}>
            Executive AI Summary
          </h3>
        </div>

        {/* Stats Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span className="clay-pill" style={{
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            background: 'var(--clay-btn-secondary-bg)',
            padding: '0.3rem 0.65rem',
            border: '1px solid var(--border-subtle)',
          }}>
            <ListOrdered size={13} color="var(--accent-cyan)" />
            {rowCount} {rowCount === 1 ? 'row' : 'rows'}
          </span>
          <span className="clay-pill" style={{
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            background: 'var(--clay-btn-secondary-bg)',
            padding: '0.3rem 0.65rem',
            border: '1px solid var(--border-subtle)',
          }}>
            <Clock size={13} color="var(--accent-emerald)" />
            {executionTimeMs?.toFixed(1) || 0} ms
          </span>
          {retryCount > 0 && (
            <span className="badge badge-warning clay-pill" style={{ fontSize: '0.68rem' }}>
              {retryCount} auto-retries
            </span>
          )}
        </div>
      </div>

      {/* Main summary text */}
      <p style={{
        fontSize: '0.94rem',
        lineHeight: '1.65',
        color: 'var(--text-primary)',
        marginBottom: insights && insights.length > 0 ? '1rem' : '0',
      }}>
        {summary}
      </p>

      {/* Key business insights */}
      {insights && insights.length > 0 && (
        <div style={{
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: '0.9rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}>
          <div style={{ fontSize: '0.76rem', fontWeight: '800', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <TrendingUp size={14} />
            <span>Key Business Insights</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.6rem' }}>
            {insights.map((ins, i) => (
              <div
                key={i}
                className="clay-pill"
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.5rem',
                  fontSize: '0.82rem',
                  color: 'var(--text-secondary)',
                  background: 'var(--clay-btn-secondary-bg)',
                  border: '1px solid var(--border-subtle)',
                  padding: '0.55rem 0.85rem',
                }}
              >
                <CheckCircle2 size={14} color="var(--accent-primary)" style={{ marginTop: '2px', flexShrink: 0 }} />
                <span>{ins}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
