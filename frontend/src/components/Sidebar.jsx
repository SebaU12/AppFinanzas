import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Wallet, Receipt, Users, CreditCard, Calculator, Settings, Landmark } from 'lucide-react';
import './Sidebar.css';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/budget', icon: Wallet, label: 'Presupuesto' },
  { path: '/transactions', icon: Receipt, label: 'Transacciones' },
  { path: '/reimbursements', icon: Users, label: 'Reembolsos' },
  { path: '/credit-cards', icon: CreditCard, label: 'Tarjetas de Crédito' },
  { path: '/debit-cards', icon: Wallet, label: 'Tarjetas de Débito' },
  { path: '/savings-cards', icon: Landmark, label: 'Tarjetas de Ahorro' },
  { path: '/simulation', icon: Calculator, label: 'Simulación' },
  { path: '/settings', icon: Settings, label: 'Configuración' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <Wallet size={32} />
        <span>Finanzas</span>
      </div>
      <nav className="sidebar-nav">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

