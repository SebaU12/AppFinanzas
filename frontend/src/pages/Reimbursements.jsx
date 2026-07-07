import { useState, useEffect } from 'react';
import { Users, Calculator, CheckCircle, XCircle } from 'lucide-react';
import { reimbursementsApi } from '../services/api';
import { getCurrentMonth } from '../utils/formatters';

export default function Reimbursements() {
  const [reimbursements, setReimbursements] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth());
  const [tempMonth, setTempMonth] = useState(getCurrentMonth()); // Temporary value for input
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReimbursements();
  }, [selectedMonth]);

  const fetchReimbursements = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await reimbursementsApi.getByMonth(selectedMonth);

      // API returns a single reimbursement object, not an array
      if (data) {
        // Map participant details with proper balance calculation
        const participantDetails = data.details?.map(detail => ({
          participantId: detail.participant_id,
          participantName: detail.participant?.name || 'Desconocido',
          amountPaid: parseFloat(detail.amount_paid || 0),
          amountReceived: parseFloat(detail.amount_received || 0),
          expectedShare: parseFloat(detail.expected_share || 0),
          balance: parseFloat(detail.balance || 0),
          percentage: parseFloat(detail.percentage || 0)
        })) || [];

        // Build summary
        setSummary({
          totalSharedExpenses: parseFloat(data.total_shared_expenses || 0),
          totalSharedIncome: parseFloat(data.total_shared_income || 0),
          participants: participantDetails,
          status: data.finalized ? 'completed' : 'pending',
          reimbursementId: data.id
        });

        setReimbursements(participantDetails);
      } else {
        setSummary(null);
        setReimbursements([]);
      }
    } catch (err) {
      // Check if it's a "not found" error (no reimbursement calculated yet)
      if (err.message && err.message.includes('not found')) {
        // This is expected - no reimbursement has been calculated for this month yet
        setError(null);
        setSummary(null);
        setReimbursements([]);
      } else {
        // Actual error - log it and show error message
        console.error('Error fetching reimbursements:', err);
        setError(err.message);
        setSummary(null);
        setReimbursements([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async () => {
    try {
      setLoading(true);
      const wasFinalized = summary?.status === 'completed';
      await reimbursementsApi.calculate(selectedMonth);
      await fetchReimbursements(); // Refresh data

      if (wasFinalized) {
        alert('¡Reembolsos recalculados correctamente! (Se eliminó la finalización anterior)');
      } else {
        alert('¡Reembolsos calculados correctamente!');
      }
    } catch (err) {
      alert('Error al calcular reembolsos: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkPaid = async () => {
    try {
      if (!summary) return;
      await reimbursementsApi.finalize(selectedMonth);
      await fetchReimbursements(); // Refresh data
      alert('¡Reembolso finalizado correctamente!');
    } catch (err) {
      alert('Error al finalizar el reembolso: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Cargando reembolsos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Reembolsos</h1>
          <p className="text-secondary">Liquidación de gastos compartidos</p>
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
        <button className="btn btn-primary" onClick={handleCalculate}>
          <Calculator size={20} />
          Calcular
        </button>
      </div>

      {/* Month Selector */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <label htmlFor="month" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
          Seleccionar mes
        </label>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            type="month"
            id="month"
            value={tempMonth}
            onChange={(e) => setTempMonth(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                setSelectedMonth(tempMonth);
              }
            }}
            className="input"
            style={{ maxWidth: '200px' }}
          />
          <button
            className="btn btn-primary"
            onClick={() => setSelectedMonth(tempMonth)}
            style={{ padding: '0.75rem 1.5rem' }}
          >
            Aplicar
          </button>
        </div>
        <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
          Haz clic en Aplicar o presiona Enter para actualizar.
        </small>
      </div>

      {/* Summary */}
      {summary && (
        <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--primary)', color: 'white' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            <Users size={32} />
            <div>
              <h2 style={{ margin: 0, marginBottom: '0.25rem' }}>Liquidación mensual</h2>
              <p style={{ margin: 0, opacity: 0.9 }}>
                Estado: {summary.status === 'completed' ? 'Finalizado' : 'Pendiente'}
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
            <div>
              <p style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Gastos compartidos brutos</p>
              <h3 style={{ margin: 0 }}>S/ {summary.totalSharedExpenses.toLocaleString()}</h3>
              {summary.totalSharedIncome > 0 && (
                <>
                  <p style={{ opacity: 0.9, marginTop: '0.75rem', marginBottom: '0.25rem' }}>Ingresos compartidos</p>
                  <h3 style={{ margin: 0 }}>- S/ {summary.totalSharedIncome.toLocaleString()}</h3>
                  <p style={{ opacity: 0.9, marginTop: '0.75rem', marginBottom: '0.25rem' }}>Gasto neto compartido</p>
                  <h3 style={{ margin: 0 }}>S/ {(summary.totalSharedExpenses - summary.totalSharedIncome).toLocaleString()}</h3>
                </>
              )}
            </div>
            {summary.participants.map(p => (
              <div key={p.participantId}>
                <p style={{ opacity: 0.9, marginBottom: '0.25rem' }}>
                  Cuota esperada de {p.participantName} ({p.percentage}%)
                </p>
                <h3 style={{ margin: 0 }}>S/ {p.expectedShare.toLocaleString()}</h3>
                <p style={{ opacity: 0.8, marginTop: '0.5rem', fontSize: '0.9rem' }}>
                  Pagó: S/ {p.amountPaid.toLocaleString()}
                  {p.amountReceived > 0 && ` • Recibió: S/ ${p.amountReceived.toLocaleString()}`}
                  {' • '}
                  Saldo: {p.balance >= 0 ? '+' : ''}S/ {p.balance.toLocaleString()}
                </p>
              </div>
            ))}
          </div>

          {summary.status === 'pending' && (
            <div style={{ marginTop: '1.5rem' }}>
              <button
                className="btn"
                onClick={handleMarkPaid}
                style={{
                  background: 'white',
                  color: 'var(--primary)',
                  border: '2px solid white'
                }}
              >
                <CheckCircle size={20} />
                Finalizar reembolso
              </button>
            </div>
          )}
        </div>
      )}

      {/* Detailed Breakdown */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Detalle por participante</h3>
        {reimbursements.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '3rem 1rem',
            color: 'var(--text-secondary)'
          }}>
            <Calculator size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
            <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Aún no se calculó ningún reembolso</p>
            <p style={{ fontSize: '0.9rem' }}>
              Haz clic en el botón "Calcular" de arriba para generar reembolsos para {selectedMonth}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--primary)' }}>
                  <th style={{ textAlign: 'left', padding: '1rem' }}>Participante</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Porcentaje</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Gastos pagados</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Ingresos recibidos</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Neto</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Cuota esperada</th>
                  <th style={{ textAlign: 'right', padding: '1rem' }}>Saldo</th>
                  <th style={{ textAlign: 'center', padding: '1rem' }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {reimbursements.map(detail => (
                  <tr key={detail.participantId} style={{ borderBottom: '1px solid #e0e0e0' }}>
                    <td style={{ padding: '1rem', fontWeight: 600 }}>{detail.participantName}</td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      {detail.percentage}%
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right', fontWeight: 600 }}>
                      S/ {detail.amountPaid.toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right', color: detail.amountReceived > 0 ? 'var(--primary)' : 'var(--text-secondary)' }}>
                      {detail.amountReceived > 0 ? `S/ ${detail.amountReceived.toLocaleString()}` : '—'}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right', fontWeight: 600 }}>
                      S/ {(detail.amountPaid - detail.amountReceived).toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      S/ {detail.expectedShare.toLocaleString()}
                    </td>
                    <td style={{
                      padding: '1rem',
                      textAlign: 'right',
                      fontWeight: 600,
                      color: detail.balance >= 0 ? 'var(--primary)' : 'var(--accent)'
                    }}>
                      {detail.balance >= 0 ? '+' : ''}S/ {detail.balance.toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      {detail.balance > 0 ? (
                        <span style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
                          <CheckCircle size={18} />
                          Le deben
                        </span>
                      ) : detail.balance < 0 ? (
                        <span style={{ color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
                          <XCircle size={18} />
                          Debe
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
                          <CheckCircle size={18} />
                          En cero
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

