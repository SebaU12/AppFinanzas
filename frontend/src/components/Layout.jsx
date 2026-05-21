import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ 
        flex: 1, 
        marginLeft: 'var(--sidebar-width)',
        transition: 'margin-left 0.3s ease'
      }}>
        <Outlet />
      </main>
    </div>
  );
}
