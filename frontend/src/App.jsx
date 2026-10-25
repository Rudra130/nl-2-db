import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SchemaExplorer from './components/SchemaExplorer';
import QueryInput from './components/QueryInput';
import SummaryCard from './components/SummaryCard';
import ResultTable from './components/ResultTable';
import QueryInspector from './components/QueryInspector';
import ErrorBanner from './components/ErrorBanner';
import {
  fetchConnections,
  testConnection,
  fetchSchema,
  executeQuery,
  fetchHealth,
} from './services/api';

export default function App() {
  const [connections, setConnections] = useState([]);
  const [activeConnectorId, setActiveConnectorId] = useState('sqlite');
  const [schema, setSchema] = useState(null);
  const [health, setHealth] = useState(null);

  // Theme State: Dark / Light
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('nl2db-theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('nl2db-theme', theme);
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);

  const [queryResult, setQueryResult] = useState(null);
  const [error, setError] = useState(null);
  const [errorStatus, setErrorStatus] = useState('error');
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [notification, setNotification] = useState(null);

  // Initial Data Load
  useEffect(() => {
    async function init() {
      try {
        const [healthData, connsData] = await Promise.all([
          fetchHealth().catch(() => null),
          fetchConnections().catch(() => []),
        ]);
        setHealth(healthData);
        setConnections(connsData);

        // Pick sqlite or first available connection
        const defaultConn = connsData.find((c) => c.id === 'sqlite') || connsData[0];
        if (defaultConn) {
          setActiveConnectorId(defaultConn.id);
          loadSchema(defaultConn.id);
        }
      } catch (err) {
        console.error('Initialization error:', err);
      }
    }
    init();
  }, []);

  const [schemaError, setSchemaError] = useState(null);

  const loadSchema = async (connectorId, force = false) => {
    setSchemaLoading(true);
    setSchemaError(null);
    try {
      const data = await fetchSchema(connectorId);
      setSchema(data);
    } catch (err) {
      setSchema(null);
      setSchemaError(err.message);
    } finally {
      setSchemaLoading(false);
    }
  };

  const handleSelectConnector = (cid) => {
    setActiveConnectorId(cid);
    loadSchema(cid);
    setError(null);
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    try {
      const res = await testConnection(activeConnectorId);
      if (res.success) {
        setNotification({ type: 'success', text: `Connected to ${res.database_type.toUpperCase()} successfully!` });
      } else {
        setNotification({ type: 'error', text: res.message });
      }
      setTimeout(() => setNotification(null), 4000);
    } catch (err) {
      setNotification({ type: 'error', text: err.message });
      setTimeout(() => setNotification(null), 4000);
    } finally {
      setTestingConnection(false);
    }
  };

  const handleRunQuery = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await executeQuery(prompt, activeConnectorId);
      setQueryResult(res);

      if (res.status === 'rejected' || res.status === 'error') {
        setError(res.error_message || 'Query execution rejected or failed.');
        setErrorStatus(res.status);
      }
    } catch (err) {
      setError(err.message);
      setErrorStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const activeConn = connections.find((c) => c.id === activeConnectorId);
  const currentDb = activeConn?.database_type || 'database';

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        connections={connections}
        activeConnectorId={activeConnectorId}
        onSelectConnector={handleSelectConnector}
        onTestConnection={handleTestConnection}
        testingConnection={testingConnection}
        health={health}
        onOpenInspector={() => setIsInspectorOpen(true)}
        hasQuery={!!queryResult?.generated_query}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* Ephemeral Notification Pill */}
      {notification && (
        <div style={{
          maxWidth: '600px',
          margin: '1rem auto 0',
          padding: '0.6rem 1rem',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.82rem',
          fontWeight: 600,
          textAlign: 'center',
          background: notification.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          color: notification.type === 'success' ? '#10b981' : '#f43f5e',
          border: `1px solid ${notification.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
          animation: 'fadeIn 0.2s ease',
        }}>
          {notification.text}
        </div>
      )}

      {/* Main Grid View */}
      <main className="main-content">
        {/* Left Column: Schema Explorer */}
        <SchemaExplorer
          schema={schema}
          loading={schemaLoading}
          error={schemaError}
          onRefresh={() => loadSchema(activeConnectorId, true)}
          activeConnectorName={activeConn?.name || ''}
          databaseType={currentDb}
        />

        {/* Right Column: Query Input, Summaries & Results */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <QueryInput
            prompt={prompt}
            setPrompt={setPrompt}
            onSubmit={handleRunQuery}
            loading={loading}
            databaseType={currentDb}
          />

          {error && (
            <ErrorBanner
              error={error}
              status={errorStatus}
              onClose={() => setError(null)}
            />
          )}

          {queryResult?.status === 'success' && (
            <SummaryCard
              summary={queryResult.summary}
              insights={queryResult.insights}
              rowCount={queryResult.row_count}
              executionTimeMs={queryResult.execution_time_ms}
              retryCount={queryResult.retry_count}
            />
          )}

          <ResultTable
            columns={queryResult?.columns || []}
            rows={queryResult?.rows || []}
            executionTimeMs={queryResult?.execution_time_ms}
          />
        </div>
      </main>

      {/* Execution Inspection Drawer */}
      <QueryInspector
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
        queryData={queryResult}
      />
    </div>
  );
}
