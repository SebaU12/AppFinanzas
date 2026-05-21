# Frontend Implementation Guide

## ✅ What's Complete

### 1. Design System & Styling (`src/index.css`)
- Complete design system with your color scheme:
  - Primary: #569B85 (teal/green)
  - Secondary: #FFC145 (warm yellow)
  - Accent: #E78484 (soft red)
  - Background: #D9F2ED (light mint)
- Typography system (Inter + Plus Jakarta Sans)
- Utility classes (grid, flex, spacing)
- Card, button, and status pill components
- Responsive breakpoints

### 2. Routing (`src/App.jsx`)
- React Router setup with 6 routes:
  - `/` → Dashboard
  - `/budget` → Budget view
  - `/transactions` → Transactions view
  - `/reimbursements` → Reimbursements view
  - `/credit-cards` → Credit Cards view
  - `/simulation` → Simulation view

### 3. Dependencies
- ✅ react, react-dom
- ✅ react-router-dom
- ✅ recharts (for charts)
- ✅ lucide-react (for icons)

## 🚧 What Needs to be Built

### Components to Create:

#### 1. `src/components/Layout.jsx`
```jsx
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, padding: '2rem', marginLeft: 'var(--sidebar-width)' }}>
        <Outlet />
      </main>
    </div>
  );
}
```

#### 2. `src/components/Sidebar.jsx`
```jsx
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Wallet, Receipt, Users, CreditCard, Calculator } from 'lucide-react';
import './Sidebar.css';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/budget', icon: Wallet, label: 'Budget' },
  { path: '/transactions', icon: Receipt, label: 'Transactions' },
  { path: '/reimbursements', icon: Users, label: 'Reimbursements' },
  { path: '/credit-cards', icon: CreditCard, label: 'Credit Cards' },
  { path: '/simulation', icon: Calculator, label: 'Simulation' },
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
```

#### 3. `src/components/Sidebar.css`
```css
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: var(--sidebar-width);
  background: var(--primary);
  border-radius: 0 40px 40px 0;
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  transition: width 0.3s ease;
}

.sidebar:hover {
  width: var(--sidebar-width-expanded);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: white;
  font-size: 1.5rem;
  font-weight: 700;
  padding: 0 0.5rem;
}

.sidebar-brand span {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.sidebar:hover .sidebar-brand span {
  opacity: 1;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  color: white;
  text-decoration: none;
  border-radius: 12px;
  transition: all 0.2s ease;
  position: relative;
}

.nav-item span {
  opacity: 0;
  white-space: nowrap;
  transition: opacity 0.3s ease;
}

.sidebar:hover .nav-item span {
  opacity: 1;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255, 255, 255, 0.2);
}

@media (max-width: 768px) {
  .sidebar {
    bottom: 0;
    top: auto;
    width: 100%;
    height: auto;
    flex-direction: row;
    border-radius: 20px 20px 0 0;
    padding: 1rem;
  }

  .sidebar-brand {
    display: none;
  }

  .sidebar-nav {
    flex-direction: row;
    width: 100%;
    justify-content: space-around;
  }

  .nav-item span {
    display: none;
  }
}
```

### Pages to Create:

#### 1. `src/pages/Dashboard.jsx` (Example with Charts)
```jsx
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, CreditCard, Users } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch from your backend API
    fetch('http://localhost:8000/statements/income-statement?start_date=2024-01-01&end_date=2024-12-31')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="container">
      <h1>Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-3 mt-3">
        <div className="card">
          <div className="flex-between">
            <div>
              <p className="text-small" style={{ color: 'var(--text-secondary)' }}>Total Income</p>
              <p className="amount" style={{ color: 'var(--success)' }}>S/. {stats?.revenues?.total || 0}</p>
            </div>
            <div className="btn-icon">
              <TrendingUp />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex-between">
            <div>
              <p className="text-small" style={{ color: 'var(--text-secondary)' }}>Total Expenses</p>
              <p className="amount" style={{ color: 'var(--error)' }}>S/. {stats?.expenses?.total || 0}</p>
            </div>
            <div className="btn-icon">
              <DollarSign />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex-between">
            <div>
              <p className="text-small" style={{ color: 'var(--text-secondary)' }}>Net Income</p>
              <p className="amount" style={{ color: 'var(--primary)' }}>S/. {stats?.net_income || 0}</p>
            </div>
            <div className="btn-icon">
              <CreditCard />
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-2 mt-4">
        <div className="card">
          <h3 className="mb-3">Monthly Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={[]}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-alt)" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="amount" stroke="var(--primary)" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="mb-3">Category Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[]}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-alt)" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="amount" fill="var(--secondary)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
```

#### 2. Template for Other Pages
```jsx
// src/pages/Budget.jsx, Transactions.jsx, etc.
import { useEffect, useState } from 'react';

export default function [PageName]() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch from backend
    fetch('http://localhost:8000/[endpoint]')
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="container">
      <h1>[Page Title]</h1>
      <div className="grid grid-2 mt-3">
        <div className="card">
          {/* Your content here */}
        </div>
      </div>
    </div>
  );
}
```

### 4. Update `src/main.jsx`
```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

## 📋 Implementation Checklist

- [ ] Create Layout.jsx
- [ ] Create Sidebar.jsx + Sidebar.css
- [ ] Create Dashboard.jsx with charts
- [ ] Create Budget.jsx
- [ ] Create Transactions.jsx with table
- [ ] Create Reimbursements.jsx
- [ ] Create CreditCards.jsx
- [ ] Create Simulation.jsx
- [ ] Update main.jsx
- [ ] Connect API calls to backend (http://localhost:8000)
- [ ] Add loading states and error handling

## 🚀 Next Steps

1. **Start the development server:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Start the backend:**
   ```bash
   cd backend
   ../.venv/bin/python -m uvicorn app.main:app --reload
   ```

3. **Build the remaining components** using the templates above

4. **Test the integration** between frontend and backend

## 🎨 Design Tokens Reference

```css
--primary: #569B85
--secondary: #FFC145
--accent: #E78484
--background: #D9F2ED
--surface: #FFFFFF
--sidebar-width: 100px
--sidebar-width-expanded: 260px
```

## 📦 Docker Integration (Next Phase)

Once frontend is complete, update `frontend/Dockerfile` and `docker-compose.yml` for containerization.
