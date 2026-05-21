import { useState, useEffect } from 'react';
import { Calculator, Plus, Trash2, TrendingDown, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { simulationApi } from '../services/api';

export default function Simulation() {
  const [expectedPurchases, setExpectedPurchases] = useState([]);
  const [simulationResult, setSimulationResult] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSimulationData();
  }, []);

  const fetchSimulationData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch expected purchases
      const purchases = await simulationApi.getAll();

      const mappedPurchases = purchases.map(p => ({
        id: p.id,
        description: p.description,
        totalAmount: parseFloat(p.total_amount),
        installments: p.installments,
        startMonth: p.start_month,
        category: p.category?.name || 'Desconocido',
        monthlyAmount: parseFloat(p.total_amount) / p.installments
      }));

      setExpectedPurchases(mappedPurchases);

      // Run simulation if there are purchases
      if (mappedPurchases.length > 0) {
        const simResult = await simulationApi.simulate();
        setSimulationResult(simResult);
      } else {
        setSimulationResult(null);
      }
    } catch (err) {
      console.error('Error fetching simulation data:', err);
      setError(err.message);
      // Fallback to mock data
      setExpectedPurchases([
        {
          id: 1,
          description: 'New Laptop',
          totalAmount: 1500,
          installments: 6,
          startMonth: '2024-03',
          category: 'Tecnologia',
          monthlyAmount: 250
        },
      ]);
      setSimulationResult({
        projectedMonths: [
          { month: 'Mar 2024', baseline: 2000, withPurchases: 2450, difference: -450 },
          { month: 'Apr 2024', baseline: 2000, withPurchases: 2650, difference: -650 },
        ],
        totalAdditionalDebt: 4700,
        monthlyAverageIncrease: 525,
        affordabilityStatus: 'warning'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    try {
      setLoading(true);
      const simResult = await simulationApi.simulate();
      setSimulationResult(simResult);
      alert('¡Simulación completada correctamente!');
    } catch (err) {
      alert('Error al ejecutar la simulación: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await simulationApi.delete(id);
      await fetchSimulationData(); // Refresh data
    } catch (err) {
      alert('Error al eliminar la compra: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Cargando datos de simulación...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Simulación de compras</h1>
          <p className="text-secondary">Planifica compras futuras y mira su impacto</p>
          {error && (
            <div style={{
              marginTop: '0.5rem',
              padding: '0.5rem',
              background: '#FFF3CD',
              border: '1px solid var(--warning)',
              borderRadius: '0.5rem',
              fontSize: '0.85rem'
            }}>
              ⚠️ Usando datos de ejemplo: {error}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn btn-secondary" onClick={handleRunSimulation}>
            <Calculator size={20} />
            Ejecutar simulación
          </button>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            <Plus size={20} />
            Agregar compra
          </button>
        </div>
      </div>

      {/* Expected Purchases List */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Compras esperadas</h3>
        {expectedPurchases.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
            No hay compras esperadas. Agrega una para empezar a simular.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--primary)' }}>
                  <th style={{ textAlign: 'left', padding: '1rem' }}>Descripción</th>
                  <th style={{ textAlign: 'left', padding: '1rem' }}>Categoría</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Monto total</th>
                  <th style={{ textAlign: 'center', padding: '1rem' }}>Cuotas</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Mensual</th>
                  <th style={{ textAlign: 'center', padding: '1rem' }}>Mes de inicio</th>
                  <th style={{ textAlign: 'center', padding: '1rem' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {expectedPurchases.map(purchase => (
                  <tr key={purchase.id} style={{ borderBottom: '1px solid #e0e0e0' }}>
                    <td style={{ padding: '1rem', fontWeight: 600 }}>{purchase.description}</td>
                    <td style={{ padding: '1rem' }}>{purchase.category}</td>
                    <td style={{ padding: '1rem', textAlign: 'right', fontWeight: 600 }}>
                      ${purchase.totalAmount.toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      {purchase.installments}x
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right', color: 'var(--accent)' }}>
                      ${purchase.monthlyAmount.toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      {new Date(purchase.startMonth + '-01').toLocaleDateString('en', { month: 'short', year: 'numeric' })}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      <button
                        className="btn-icon"
                        title="Eliminar"
                        onClick={() => handleDelete(purchase.id)}
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Simulation Results */}
      {simulationResult && (
        <>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="card" style={{ background: 'var(--accent)', color: 'white' }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Deuda adicional total</p>
              <h2 style={{ margin: 0 }}>${simulationResult.totalAdditionalDebt.toLocaleString()}</h2>
            </div>
            <div className="card" style={{ background: 'var(--secondary)', color: 'white' }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Promedio mensual</p>
              <h2 style={{ margin: 0 }}>${simulationResult.monthlyAverageIncrease.toLocaleString()}</h2>
            </div>
            <div className="card" style={{
              background: simulationResult.affordabilityStatus === 'safe' ? 'var(--primary)' :
                          simulationResult.affordabilityStatus === 'warning' ? 'var(--secondary)' :
                          'var(--accent)',
              color: 'white'
            }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Asequibilidad</p>
              <h2 style={{ margin: 0, textTransform: 'capitalize' }}>
                {simulationResult.affordabilityStatus}
              </h2>
            </div>
          </div>

          {/* Warning Alert */}
          {simulationResult.affordabilityStatus !== 'safe' && (
            <div
              className="card"
              style={{
                background: '#FFF3CD',
                border: '2px solid var(--secondary)',
                marginBottom: '1.5rem'
              }}
            >
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                <AlertCircle size={24} style={{ color: 'var(--secondary)', flexShrink: 0 }} />
                <div>
                  <h4 style={{ margin: 0, marginBottom: '0.5rem', color: '#856404' }}>
                    Advertencia de impacto en el presupuesto
                  </h4>
                  <p style={{ margin: 0, color: '#856404' }}>
                    Estas compras afectarán significativamente tu presupuesto mensual. Considera distribuirlas en más meses o ajustar tu gasto en otras categorías.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Projection Chart */}
          <div className="card">
            <h3 style={{ marginBottom: '1rem' }}>Proyección de flujo de caja a 6 meses</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={simulationResult.projectedMonths}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="baseline"
                  stroke="var(--primary)"
                  strokeWidth={2}
                  name="Base actual"
                />
                <Line
                  type="monotone"
                  dataKey="withPurchases"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  name="Con nuevas compras"
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Monthly Breakdown */}
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Detalle del impacto mensual</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--primary)' }}>
                    <th style={{ textAlign: 'left', padding: '1rem' }}>Mes</th>
                    <th style={{ textAlign: 'right', padding: '1rem' }}>Gastos actuales</th>
                    <th style={{ textAlign: 'right', padding: '1rem' }}>Con compras</th>
                    <th style={{ textAlign: 'right', padding: '1rem' }}>Diferencia</th>
                    <th style={{ textAlign: 'center', padding: '1rem' }}>Impacto</th>
                  </tr>
                </thead>
                <tbody>
                  {simulationResult.projectedMonths.map((month, idx) => {
                    const impactPercent = ((month.difference / month.baseline) * 100).toFixed(1);

                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid #e0e0e0' }}>
                        <td style={{ padding: '1rem', fontWeight: 600 }}>{month.month}</td>
                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                          ${month.baseline.toLocaleString()}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right', color: 'var(--accent)', fontWeight: 600 }}>
                          ${month.withPurchases.toLocaleString()}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right', color: 'var(--accent)', fontWeight: 600 }}>
                          ${Math.abs(month.difference).toLocaleString()}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                            <TrendingDown size={18} style={{ color: 'var(--accent)' }} />
                            <span style={{ color: 'var(--accent)', fontWeight: 600 }}>
                              {Math.abs(parseFloat(impactPercent))}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

