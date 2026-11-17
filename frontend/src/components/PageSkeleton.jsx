import React from 'react';
import './PageSkeleton.css';

export default function PageSkeleton() {
  return (
    <div className="skeleton-page-wrapper">
      {/* Top Header Shimmer */}
      <div className="skeleton-glass-card skeleton-header-card">
        <div className="skeleton-line skeleton-badge shimmer" />
        <div className="skeleton-line skeleton-title shimmer" />
        <div className="skeleton-line skeleton-subtitle shimmer" />
      </div>

      {/* Metric / Stat Blocks Row */}
      <div className="skeleton-grid-row">
        <div className="skeleton-glass-card skeleton-stat-card">
          <div className="skeleton-line skeleton-stat-num shimmer" />
          <div className="skeleton-line skeleton-stat-label shimmer" />
        </div>
        <div className="skeleton-glass-card skeleton-stat-card">
          <div className="skeleton-line skeleton-stat-num shimmer" />
          <div className="skeleton-line skeleton-stat-label shimmer" />
        </div>
        <div className="skeleton-glass-card skeleton-stat-card">
          <div className="skeleton-line skeleton-stat-num shimmer" />
          <div className="skeleton-line skeleton-stat-label shimmer" />
        </div>
      </div>

      {/* Main Content Dual Glass Cards */}
      <div className="skeleton-main-grid">
        <div className="skeleton-glass-card skeleton-content-card">
          <div className="skeleton-card-header">
            <div className="skeleton-avatar shimmer" />
            <div className="skeleton-line skeleton-card-title shimmer" />
          </div>
          <div className="skeleton-body-lines">
            <div className="skeleton-line shimmer" style={{ width: '100%' }} />
            <div className="skeleton-line shimmer" style={{ width: '92%' }} />
            <div className="skeleton-line shimmer" style={{ width: '78%' }} />
            <div className="skeleton-line shimmer" style={{ width: '85%' }} />
          </div>
          <div className="skeleton-footer-pills">
            <div className="skeleton-pill shimmer" />
            <div className="skeleton-pill shimmer" />
          </div>
        </div>

        <div className="skeleton-glass-card skeleton-content-card">
          <div className="skeleton-card-header">
            <div className="skeleton-avatar shimmer" />
            <div className="skeleton-line skeleton-card-title shimmer" />
          </div>
          <div className="skeleton-body-lines">
            <div className="skeleton-line shimmer" style={{ width: '95%' }} />
            <div className="skeleton-line shimmer" style={{ width: '88%' }} />
            <div className="skeleton-line shimmer" style={{ width: '70%' }} />
            <div className="skeleton-line shimmer" style={{ width: '60%' }} />
          </div>
          <div className="skeleton-footer-pills">
            <div className="skeleton-pill shimmer" />
            <div className="skeleton-pill shimmer" />
          </div>
        </div>
      </div>
    </div>
  );
}
