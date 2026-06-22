import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, CreditCard, Wallet } from 'lucide-react';
import { transactionsApi, reimbursementsApi, participantsApi, cashFlowApi, debitCardsApi } from '../services/api';
import { getCurrentMonth, formatCurrency } from '../utils/formatters';

const COLORS = ['#569B85', '#FFC145', '#E78484', '#A7CDC1', '#FFE3A3'];

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalIncome: 0,
    totalExpenses: 0,
    balance: 0,
    pendingReimbursements: 0,
    availableCash: 0,
    pendingCreditPayments: 0
  });
  const [monthlyData, setMonthlyData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [selectedParticipant, setSelectedParticipant] = useState('all');
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth());
  const [tempMonth, setTempMonth] = useState(getCurrentMonth()); // Temporary value for input
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchParticipants();
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedParticipant, selectedMonth]);

  const fetchParticipants = async () => {
    try {
      const data = await participantsApi.getAll();
      setParticipants(data);
    } catch (err) {
      console.error('Error fetching participants:', err);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch transactions for selected month
      const allTransactions = await transactionsApi.getByMonth(selectedMonth);

      // Filter by selected participant
      const transactions = selectedParticipant === 'all'
        ? allTransactions
        : allTransactions.filter(t => t.participant?.name === selectedParticipant);

      // Calculate stats from transactions
      const income = transactions
        .filter(t => t.category?.type === 'income')
        .reduce((sum, t) => sum + parseFloat(t.amount), 0);

      const expenses = transactions
        .filter(t => t.category?.type === 'expense')
        .reduce((sum, t) => sum + parseFloat(t.amount), 0);

      // Fetch reimbursement data
      let pendingReimbursement = 0;
      try {
        const reimbursement = await reimbursementsApi.getByMonth(selectedMonth);

        if (selectedParticipant === 'all') {
          // For "all" view, show total settlement amount needed
          pendingReimbursement = reimbursement.details
            ?.reduce((sum, d) => sum + Math.abs(parseFloat(d.balance || 0)), 0) / 2 || 0;
          // Divide by 2 because each balance is counted twice (one positive, one negative)
        } else {
          // For specific participant, show their balance
          const participantDetail = reimbursement.details
            ?.find(d => d.participant?.name === selectedParticipant);
          pendingReimbursement = parseFloat(participantDetail?.balance || 0);
        }
      } catch (err) {
        // No reimbursement calculated yet or error - leave at 0
        console.log('No reimbursement data available');
      }

      // Fetch debit cards for available cash
      let availableCash = 0;
      try {
        const debitCards = await debitCardsApi.getAll();

        if (selectedParticipant === 'all') {
          // Sum all debit card balances
          availableCash = debitCards.reduce((sum, card) =>
            sum + parseFloat(card.current_balance || 0), 0);
        } else {
          // Sum only cards belonging to selected participant
          availableCash = debitCards
            .filter(card => card.participant?.name === selectedParticipant)
            .reduce((sum, card) => sum + parseFloat(card.current_balance || 0), 0);
        }
      } catch (err) {
        console.log('Error fetching debit cards:', err);
      }

      // Fetch pending credit payments
      let pendingCreditPayments = 0;
      try {
        const cashFlowData = await cashFlowApi.getSummary(selectedMonth);
        pendingCreditPayments = cashFlowData.pending_credit_payments || 0;
      } catch (err) {
        console.log('No cash flow data available');
      }

      setStats({
        totalIncome: income,
        totalExpenses: expenses,
        balance: income - expenses,
        pendingReimbursements: pendingReimbursement,
        availableCash: availableCash,
        pendingCreditPayments: pendingCreditPayments
      });

      // Group expenses by category
      const categoryMap = {};
      transactions
        .filter(t => t.category?.type === 'expense')
        .forEach(t => {
          const catName = t.category?.name || 'Other';
          categoryMap[catName] = (categoryMap[catName] || 0) + parseFloat(t.amount);
        });

      const categoryArray = Object.entries(categoryMap)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 5); // Top 5 categories

      setCategoryData(categoryArray);

      // Mock monthly data for now (TODO: Implement proper monthly aggregation)
      setMonthlyData([
        { month: 'Current', income, expenses },
      ]);

    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err.message);
      // Fallback to mock data on error
      setStats({
        totalIncome: 5000,
        totalExpenses: 3200,
        balance: 1800,
        pendingReimbursements: 450,
        availableCash: 1200,
        pendingCreditPayments: 600
      });
      setMonthlyData([
        { month: 'Jan', income: 4500, expenses: 3200 },
        { month: 'Feb', income: 4800, expenses: 3500 },
        { month: 'Mar', income: 5000, expenses: 3200 },
      ]);
      setCategoryData([
        { name: 'Alimentacion', value: 800 },
        { name: 'Transporte', value: 400 },
        { name: 'Vivienda', value: 1200 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Cargando datos del panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="text-secondary">Resumen financiero</p>
        </div>
        {error && (
          <div style={{
            padding: '0.75rem 1rem',
            background: '#FFF3CD',
            border: '2px solid var(--warning)',
            borderRadius: '0.5rem',
            fontSize: '0.9rem'
          }}>
            ⚠️ Usando datos de ejemplo: {error}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', alignItems: 'end' }}>
          <div>
            <label htmlFor="month-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
              Mes
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                id="month-filter"
                type="month"
                className="input"
                value={tempMonth}
                onChange={(e) => setTempMonth(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    setSelectedMonth(tempMonth);
                  }
                }}
                style={{ flex: 1 }}
              />
              <button
                className="btn btn-primary"
                onClick={() => setSelectedMonth(tempMonth)}
                style={{ padding: '0.75rem 1.5rem' }}
              >
                Aplicar
              </button>
            </div>
          </div>
          <div>
            <label htmlFor="participant-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
              Participante
            </label>
            <select
              id="participant-filter"
              className="input"
              value={selectedParticipant}
              onChange={(e) => setSelectedParticipant(e.target.value)}
            >
              <option value="all">Todos los participantes</option>
              {participants.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card" style={{ background: 'linear-gradient(135deg, var(--primary), var(--primary-dark))' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '0.5rem' }}>Ingresos totales</p>
              <h2 style={{ color: 'white', margin: 0 }}>S/ {stats.totalIncome.toLocaleString()}</h2>
            </div>
            <TrendingUp size={32} style={{ color: 'rgba(255,255,255,0.8)' }} />
          </div>
        </div>

        <div className="card" style={{ background: 'linear-gradient(135deg, var(--accent), #c66666)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '0.5rem' }}>Gastos totales</p>
              <h2 style={{ color: 'white', margin: 0 }}>S/ {stats.totalExpenses.toLocaleString()}</h2>
              <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: '0.25rem', fontSize: '0.75rem' }}>
                Lo que consumiste
              </p>
            </div>
            <TrendingDown size={32} style={{ color: 'rgba(255,255,255,0.8)' }} />
          </div>
        </div>

        <div className="card" style={{ background: 'linear-gradient(135deg, #2d5f7a, #1e4057)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '0.5rem' }}>Efectivo disponible</p>
              <h2 style={{ color: 'white', margin: 0 }}>
                S/ {stats.availableCash.toLocaleString()}
              </h2>
              <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: '0.25rem', fontSize: '0.75rem' }}>
                Posición real de dinero
              </p>
            </div>
            <Wallet size={32} style={{ color: 'rgba(255,255,255,0.8)' }} />
          </div>
        </div>

        <div className="card" style={{ background: 'linear-gradient(135deg, var(--secondary), #e6a830)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '0.5rem' }}>Saldo del presupuesto</p>
              <h2 style={{ color: 'white', margin: 0 }}>S/ {stats.balance.toLocaleString()}</h2>
              <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: '0.25rem', fontSize: '0.75rem' }}>
                Vista 
              </p>
            </div>
            <DollarSign size={32} style={{ color: 'rgba(255,255,255,0.8)' }} />
          </div>
        </div>

        <div className="card" style={{
          background: selectedParticipant === 'all'
            ? 'linear-gradient(135deg, var(--primary-light), var(--primary))'
            : stats.pendingReimbursements >= 0
              ? 'linear-gradient(135deg, #569B85, #3d7a61)'
              : 'linear-gradient(135deg, var(--accent), #c66666)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '0.5rem' }}>
                {selectedParticipant === 'all'
                  ? 'Reembolsos pendientes'
                  : stats.pendingReimbursements >= 0
                    ? 'Te deben'
                    : 'Debes'}
              </p>
              <h2 style={{ color: 'white', margin: 0 }}>
                {stats.pendingReimbursements >= 0 ? '+' : ''}S/ {Math.abs(stats.pendingReimbursements).toLocaleString()}
              </h2>
            </div>
            <CreditCard size={32} style={{ color: 'rgba(255,255,255,0.8)' }} />
          </div>
        </div>

        <div className="card" style={{ background: 'linear-gradient(135deg, #8a5a44, #5c3a2e)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '0.5rem' }}>Pagos pendientes de crédito</p>
              <h2 style={{ color: 'white', margin: 0 }}>
                S/ {stats.pendingCreditPayments.toLocaleString()}
              </h2>
              <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: '0.25rem', fontSize: '0.75rem' }}>
                Cuotas sin pagar
              </p>
            </div>
            <CreditCard size={32} style={{ color: 'rgba(255,255,255,0.8)' }} />
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Monthly Income vs Expenses */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Ingresos vs Gastos</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="income" fill="var(--primary)" />
              <Bar dataKey="expenses" fill="var(--accent)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Category Breakdown */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Gastos por categoría</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Tendencia de gasto</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="expenses" stroke="var(--accent)" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

