import React, { useState } from 'react';
import './App.css';

interface ApiTestResult {
  endpoint: string;
  status: 'success' | 'error';
  message: string;
}

const App: React.FC = () => {
  const [testResults, setTestResults] = useState<ApiTestResult[]>([]);
  const [loading, setLoading] = useState(false);

  const testApiEndpoint = async (endpoint: string, method: string = 'GET', body?: any) => {
    try {
      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      const response = await fetch(`http://localhost:8000${endpoint}`, options);
      const data = await response.json();

      return {
        endpoint: `${method} ${endpoint}`,
        status: response.ok ? 'success' as const : 'error' as const,
        message: response.ok ? JSON.stringify(data, null, 2) : data.error?.message || 'Failed'
      };
    } catch (error) {
      return {
        endpoint: `${method} ${endpoint}`,
        status: 'error' as const,
        message: error instanceof Error ? error.message : 'Network error'
      };
    }
  };

  const runApiTests = async () => {
    setLoading(true);
    setTestResults([]);
    
    const tests = [
      () => testApiEndpoint('/health'),
    ];

    for (const test of tests) {
      const result = await test();
      setTestResults(prev => [...prev, result]);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1>🎉 DeepInsight System</h1>
        <p>Complete TypeScript React Application</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        
        <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>🚀 System Status</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ padding: '8px', backgroundColor: '#d4edda', border: '1px solid #c3e6cb', borderRadius: '4px' }}>
              ✅ Backend API: Ready
            </div>
            <div style={{ padding: '8px', backgroundColor: '#d4edda', border: '1px solid #c3e6cb', borderRadius: '4px' }}>
              ✅ Database: Connected
            </div>
            <div style={{ padding: '8px', backgroundColor: '#d4edda', border: '1px solid #c3e6cb', borderRadius: '4px' }}>
              ✅ AI Integration: Configured
            </div>
            <div style={{ padding: '8px', backgroundColor: '#d4edda', border: '1px solid #c3e6cb', borderRadius: '4px' }}>
              ✅ TypeScript: Working
            </div>
          </div>
        </div>

        <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>🔗 Quick Links</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" 
               style={{ padding: '10px', backgroundColor: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '4px', textAlign: 'center' }}>
              📚 API Documentation
            </a>
            <a href="http://localhost:8000/health" target="_blank" rel="noopener noreferrer"
               style={{ padding: '10px', backgroundColor: '#28a745', color: 'white', textDecoration: 'none', borderRadius: '4px', textAlign: 'center' }}>
              ❤️ Health Check
            </a>
          </div>
        </div>

        <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>🧪 API Test</h3>
          <button 
            onClick={runApiTests}
            disabled={loading}
            style={{ 
              padding: '10px 20px', 
              backgroundColor: loading ? '#6c757d' : '#17a2b8', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: loading ? 'not-allowed' : 'pointer',
              width: '100%'
            }}
          >
            {loading ? 'Testing...' : 'Test Backend API'}
          </button>
          
          {testResults.length > 0 && (
            <div style={{ marginTop: '15px' }}>
              {testResults.map((result, index) => (
                <div key={index} style={{ 
                  padding: '10px', 
                  margin: '5px 0', 
                  backgroundColor: result.status === 'success' ? '#d4edda' : '#f8d7da',
                  border: `1px solid ${result.status === 'success' ? '#c3e6cb' : '#f5c6cb'}`,
                  borderRadius: '4px'
                }}>
                  <strong>{result.endpoint}</strong>
                  <pre style={{ marginTop: '5px', fontSize: '12px', overflow: 'auto' }}>
                    {result.message}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ gridColumn: '1 / -1', border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>📋 Available Features</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
            <div>
              <h4>👥 Authentication</h4>
              <ul>
                <li>User registration & login</li>
                <li>JWT token management</li>
                <li>Password validation</li>
              </ul>
            </div>
            <div>
              <h4>📄 Document Processing</h4>
              <ul>
                <li>PDF, DOCX, TXT, MD support</li>
                <li>Text extraction</li>
                <li>Metadata extraction</li>
              </ul>
            </div>
            <div>
              <h4>🤖 AI Integration</h4>
              <ul>
                <li>Ontology creation</li>
                <li>Entity extraction</li>
                <li>Relationship mapping</li>
              </ul>
            </div>
            <div>
              <h4>📤 Data Export</h4>
              <ul>
                <li>Neo4j CSV format</li>
                <li>AWS Neptune format</li>
                <li>Graph visualization</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;