import React from 'react';
import { FiAlertTriangle, FiRefreshCw } from 'react-icons/fi';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Signal Stack UI caught an error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', maxWidth: '600px', margin: '40px auto', textAlign: 'center' }} className="card">
          <FiAlertTriangle style={{ fontSize: '48px', color: 'var(--error)', marginBottom: '16px' }} />
          <h2>Something went wrong loading this view</h2>
          <p style={{ color: 'var(--tertiary)', fontSize: '15px', margin: '12px 0 24px' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred.'}
          </p>
          <button className="btn-primary" onClick={this.handleReload}>
            <FiRefreshCw style={{ marginRight: 6 }} /> Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
