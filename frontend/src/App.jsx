import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Budget from './pages/Budget';
import Transactions from './pages/Transactions';
import Reimbursements from './pages/Reimbursements';
import CreditCards from './pages/CreditCards';
import DebitCards from './pages/DebitCards';
import Simulation from './pages/Simulation';
import Settings from './pages/Settings';
import './index.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="budget" element={<Budget />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="reimbursements" element={<Reimbursements />} />
          <Route path="credit-cards" element={<CreditCards />} />
          <Route path="debit-cards" element={<DebitCards />} />
          <Route path="simulation" element={<Simulation />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
