import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Edit, Trash2, Download, X, Save } from 'lucide-react';
import { transactionsApi, participantsApi, categoriesApi, creditCardsApi, debitCardsApi } from '../services/api';
import { getCurrentMonth, formatLocalDate } from '../utils/formatters';

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [categories, setCategories] = useState([]);
  const [creditCards, setCreditCards] = useState([]);
  const [debitCards, setDebitCards] = useState([]);
  const [filters, setFilters] = useState({
    search: '',
    type: 'all',
    category: 'all',
    participant: 'all',
    dateFrom: '',
    dateTo: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryStep, setCategoryStep] = useState(1); // 1 = select parent, 2 = select subcategory
  const [selectedParentCategory, setSelectedParentCategory] = useState(null);
  const [transactionForm, setTransactionForm] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: '',
    category_id: '',
    participant_id: '',
    payment_method: 'cash',
    card_id: '',
    debit_card_id: '',
    installments: 1,
    description: ''
  });

  useEffect(() => {
    fetchTransactions();
    fetchFormData();
  }, []);

  const fetchFormData = async () => {
    try {
      const [participantsData, categoriesData, creditCardsData, debitCardsData] = await Promise.all([
        participantsApi.getAll(),
        categoriesApi.getAll(),
        creditCardsApi.getAll(),
        debitCardsApi.getAll()
      ]);
      setParticipants(participantsData);
      setCategories(categoriesData);
      setCreditCards(creditCardsData);
      setDebitCards(debitCardsData);
    } catch (err) {
      console.error('Error fetching form data:', err);
    }
  };

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch current month transactions by default
      const currentMonth = getCurrentMonth();
      const data = await transactionsApi.getByMonth(currentMonth);

      // Map API response to component format
      const mappedData = data.map(t => ({
        id: t.id,
        date: t.date,
        description: t.description,
        category: t.category?.name || 'Desconocido',
        subcategory: t.subcategory || null,
        type: t.category?.type || t.type,
        amount: parseFloat(t.amount),
        participant: t.participant?.name || 'Desconocido',
        paymentMethod: t.payment_method
      }));

      setTransactions(mappedData);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError(err.message);
      // No fallback - show empty state
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTransaction = () => {
    setTransactionForm({
      date: new Date().toISOString().split('T')[0],
      amount: '',
      category_id: '',
      participant_id: participants[0]?.id || '',
      payment_method: 'cash',
      card_id: '',
      installments: 1,
      description: ''
    });
    setEditingTransaction(null);
    setCategoryStep(1);
    setSelectedParentCategory(null);
    setShowModal(true);
  };

  const handleSaveTransaction = async () => {
    try {
      const payload = {
        date: transactionForm.date,
        amount: parseFloat(transactionForm.amount),
        category_id: transactionForm.category_id,
        participant_id: transactionForm.participant_id,
        payment_method: transactionForm.payment_method,
        description: transactionForm.description
      };

      // Add debit_card_id if payment method is debit and card selected
      if (transactionForm.payment_method === 'debit' && transactionForm.debit_card_id) {
        payload.debit_card_id = transactionForm.debit_card_id;
      }

      // Add card_id and installment_count only if payment method is credit
      if (transactionForm.payment_method === 'credit') {
        payload.card_id = transactionForm.card_id;
        payload.installment_count = parseInt(transactionForm.installments);
      }

      if (editingTransaction) {
        await transactionsApi.update(editingTransaction.id, payload);
      } else {
        await transactionsApi.create(payload);
      }

      setShowModal(false);
      setEditingTransaction(null);
      setCategoryStep(1);
      setSelectedParentCategory(null);
      await fetchTransactions();
    } catch (err) {
      alert('Error al guardar la transacción: ' + err.message);
    }
  };

  const handleDeleteTransaction = async (transaction) => {
    if (window.confirm(`¿Seguro que quieres eliminar esta transacción?`)) {
      try {
        await transactionsApi.delete(transaction.id);
        await fetchTransactions();
      } catch (err) {
        alert('Error al eliminar la transacción: ' + err.message);
      }
    }
  };

  const filteredTransactions = transactions.filter(t => {
    if (filters.search && !t.description.toLowerCase().includes(filters.search.toLowerCase())) {
      return false;
    }
    if (filters.type !== 'all' && t.type !== filters.type) {
      return false;
    }
    if (filters.participant !== 'all' && t.participant !== filters.participant) {
      return false;
    }
    if (filters.dateFrom && t.date < filters.dateFrom) {
      return false;
    }
    if (filters.dateTo && t.date > filters.dateTo) {
      return false;
    }
    return true;
  });

  const totalIncome = filteredTransactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpenses = filteredTransactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0);

  if (loading) {
    return (
      <div className="page">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Cargando transacciones...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Transacciones</h1>
          <p className="text-secondary">Todos los ingresos y gastos</p>
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
          <button className="btn btn-secondary" onClick={() => setShowFilters(!showFilters)}>
            <Filter size={20} />
            Filtros
          </button>
          <button className="btn btn-primary" onClick={handleAddTransaction}>
            <Plus size={20} />
            Nueva transacción
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ background: 'var(--primary)', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Ingresos totales</p>
          <h2 style={{ margin: 0 }}>${totalIncome.toLocaleString()}</h2>
        </div>
        <div className="card" style={{ background: 'var(--accent)', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Gastos totales</p>
          <h2 style={{ margin: 0 }}>${totalExpenses.toLocaleString()}</h2>
        </div>
        <div className="card" style={{ background: 'var(--secondary)', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Neto</p>
          <h2 style={{ margin: 0 }}>${(totalIncome - totalExpenses).toLocaleString()}</h2>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                Buscar
              </label>
              <div style={{ position: 'relative' }}>
                <Search size={18} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#999' }} />
                <input
                  type="text"
                  className="input"
                  placeholder="Buscar descripción..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  style={{ paddingLeft: '2.5rem' }}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                Tipo
              </label>
              <select
                className="input"
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
              >
                <option value="all">Todos</option>
                <option value="income">Ingreso</option>
                <option value="expense">Gasto</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                Participante
              </label>
              <select
                className="input"
                value={filters.participant}
                onChange={(e) => setFilters({ ...filters, participant: e.target.value })}
              >
                <option value="all">Todos los participantes</option>
                {participants.map((p) => (
                  <option key={p.id} value={p.name}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                Fecha desde
              </label>
              <input
                type="date"
                className="input"
                value={filters.dateFrom}
                onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                Fecha hasta
              </label>
              <input
                type="date"
                className="input"
                value={filters.dateTo}
                onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
              />
            </div>
          </div>
        </div>
      )}

      {/* Transactions Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0 }}>Transacciones recientes</h3>
          <button className="btn-icon" title="Exportar">
            <Download size={20} />
          </button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--primary)' }}>
                <th style={{ textAlign: 'left', padding: '1rem' }}>Fecha</th>
                <th style={{ textAlign: 'left', padding: '1rem' }}>Descripción</th>
                <th style={{ textAlign: 'left', padding: '1rem' }}>Categoría</th>
                <th style={{ textAlign: 'left', padding: '1rem' }}>Tipo</th>
                <th style={{ textAlign: 'left', padding: '1rem' }}>Participante</th>
                <th style={{ textAlign: 'right', padding: '1rem' }}>Monto</th>
                <th style={{ textAlign: 'center', padding: '1rem' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map(transaction => (
                <tr key={transaction.id} style={{ borderBottom: '1px solid #e0e0e0' }}>
                  <td style={{ padding: '1rem' }}>
                    {formatLocalDate(transaction.date)}
                  </td>
                  <td style={{ padding: '1rem', fontWeight: 600 }}>{transaction.description}</td>
                  <td style={{ padding: '1rem' }}>
                    <div>{transaction.category}</div>
                    {transaction.subcategory && (
                      <div style={{ fontSize: '0.875rem', color: '#666' }}>{transaction.subcategory}</div>
                    )}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span className="badge" style={{
                      background: transaction.type === 'income' ? 'var(--primary)' : 'var(--accent)',
                      color: 'white'
                    }}>
                      {transaction.type === 'income' ? 'Ingreso' : 'Gasto'}
                    </span>
                  </td>
                  <td style={{ padding: '1rem' }}>{transaction.participant}</td>
                  <td style={{
                    padding: '1rem',
                    textAlign: 'right',
                    fontWeight: 600,
                    color: transaction.type === 'income' ? 'var(--primary)' : 'var(--accent)'
                  }}>
                    {transaction.type === 'income' ? '+' : '-'}${transaction.amount.toLocaleString()}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center' }}>
                    <button className="btn-icon" title="Editar">
                      <Edit size={18} />
                    </button>
                    <button className="btn-icon" title="Eliminar" style={{ marginLeft: '0.5rem' }}>
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal for Add/Edit Transaction */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={() => setShowModal(false)}
        >
          <div
            className="card"
            style={{
              maxWidth: '600px',
              width: '90%',
              maxHeight: '90vh',
              overflow: 'auto'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>{editingTransaction ? 'Editar transacción' : 'Nueva transacción'}</h2>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '0.5rem',
                  display: 'flex'
                }}
              >
                <X size={24} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Fecha *
                  </label>
                  <input
                    type="date"
                    value={transactionForm.date}
                    onChange={(e) => setTransactionForm({ ...transactionForm, date: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '0.5rem',
                      fontSize: '1rem'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Monto *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={transactionForm.amount}
                    onChange={(e) => setTransactionForm({ ...transactionForm, amount: e.target.value })}
                    placeholder="0.00"
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '0.5rem',
                      fontSize: '1rem'
                    }}
                  />
                </div>
              </div>

              {/* Category Selection - Step 1: Parent Category */}
              {categoryStep === 1 && (
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Seleccionar tipo de categoría *
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
                    {categories
                      .filter(cat => cat.parent_id === null)
                      .map((parentCat) => (
                        <button
                          key={parentCat.id}
                          type="button"
                          onClick={() => {
                            setSelectedParentCategory(parentCat);
                            setCategoryStep(2);
                          }}
                          style={{
                            padding: '1rem',
                            border: '2px solid #ddd',
                            borderRadius: '0.5rem',
                            background: 'white',
                            cursor: 'pointer',
                            fontSize: '0.95rem',
                            fontWeight: 600,
                            transition: 'all 0.2s',
                            textAlign: 'left'
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.borderColor = 'var(--primary)';
                            e.target.style.background = '#f8f9fa';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.borderColor = '#ddd';
                            e.target.style.background = 'white';
                          }}
                        >
                          {parentCat.name}
                          <div style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.25rem' }}>
                            {parentCat.type === 'income' ? 'Ingreso' : 'Gasto'}
                          </div>
                        </button>
                      ))}
                  </div>
                </div>
              )}

              {/* Category Selection - Step 2: Subcategory */}
              {categoryStep === 2 && selectedParentCategory && (
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    {selectedParentCategory.name} - Seleccionar subcategoría *
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setCategoryStep(1);
                      setSelectedParentCategory(null);
                      setTransactionForm({ ...transactionForm, category_id: '' });
                    }}
                    style={{
                      marginBottom: '0.75rem',
                      padding: '0.5rem 1rem',
                      background: '#f8f9fa',
                      border: '1px solid #ddd',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      fontSize: '0.875rem'
                    }}
                  >
                    ← Volver a categorías
                  </button>
                  <select
                    value={transactionForm.category_id}
                    onChange={(e) => setTransactionForm({ ...transactionForm, category_id: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '0.5rem',
                      fontSize: '1rem'
                    }}
                  >
                    <option value="">Seleccionar subcategoría</option>
                    {categories
                      .filter(cat => cat.parent_id === selectedParentCategory.id)
                      .map((subcat) => (
                        <option key={subcat.id} value={subcat.id}>
                          {subcat.name}
                        </option>
                      ))}
                  </select>
                </div>
              )}

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Participante *
                </label>
                <select
                  value={transactionForm.participant_id}
                  onChange={(e) => setTransactionForm({
                    ...transactionForm,
                    participant_id: e.target.value,
                    card_id: '', // Clear card selection when participant changes
                    debit_card_id: '' // Clear debit card selection when participant changes
                  })}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '0.5rem',
                    fontSize: '1rem'
                  }}
                >
                  <option value="">Seleccionar participante</option>
                  {participants.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Método de pago *
                </label>
                <select
                  value={transactionForm.payment_method}
                  onChange={(e) => setTransactionForm({ ...transactionForm, payment_method: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '0.5rem',
                    fontSize: '1rem'
                  }}
                >
                  <option value="cash">Efectivo</option>
                  <option value="debit">Tarjeta de débito</option>
                  <option value="credit">Tarjeta de crédito</option>
                </select>
              </div>

              {transactionForm.payment_method === 'debit' && (
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Tarjeta de débito / Cuenta bancaria
                  </label>
                  <select
                    value={transactionForm.debit_card_id}
                    onChange={(e) => setTransactionForm({ ...transactionForm, debit_card_id: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '0.5rem',
                      fontSize: '1rem'
                    }}
                  >
                    <option value="">Seleccionar tarjeta de débito (opcional)</option>
                    {debitCards
                      .filter(card => card.participant_id === transactionForm.participant_id)
                      .map((card) => (
                        <option key={card.id} value={card.id}>
                          {card.name} - ${parseFloat(card.current_balance || 0).toLocaleString()}
                        </option>
                      ))}
                  </select>
                  {debitCards.filter(card => card.participant_id === transactionForm.participant_id).length === 0 ? (
                    <small style={{ display: 'block', marginTop: '0.25rem', color: '#E78484' }}>
                      ⚠️ No hay tarjetas de débito disponibles para este participante
                    </small>
                  ) : (
                    <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
                      Opcional: vincular a una cuenta bancaria específica
                    </small>
                  )}
                </div>
              )}

              {transactionForm.payment_method === 'credit' && (
                <>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                      Tarjeta de crédito *
                    </label>
                    <select
                      value={transactionForm.card_id}
                      onChange={(e) => setTransactionForm({ ...transactionForm, card_id: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: '1px solid #ddd',
                        borderRadius: '0.5rem',
                        fontSize: '1rem'
                      }}
                    >
                      <option value="">Seleccionar tarjeta de crédito</option>
                      {creditCards
                        .filter(card => card.participant_id === transactionForm.participant_id)
                        .map((card) => (
                          <option key={card.id} value={card.id}>
                            {card.name}
                          </option>
                        ))}
                    </select>
                    {creditCards.filter(card => card.participant_id === transactionForm.participant_id).length === 0 && (
                      <small style={{ display: 'block', marginTop: '0.25rem', color: '#E78484' }}>
                        ⚠️ No hay tarjetas de crédito disponibles para este participante
                      </small>
                    )}
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                      Cuotas *
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="36"
                      value={transactionForm.installments}
                      onChange={(e) => setTransactionForm({ ...transactionForm, installments: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: '1px solid #ddd',
                        borderRadius: '0.5rem',
                        fontSize: '1rem'
                      }}
                    />
                    <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
                      Número de pagos mensuales (1-36)
                    </small>
                  </div>
                </>
              )}

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Descripción
                </label>
                <textarea
                  value={transactionForm.description}
                  onChange={(e) => setTransactionForm({ ...transactionForm, description: e.target.value })}
                  placeholder="Notas opcionales sobre esta transacción"
                  rows="3"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '0.5rem',
                    fontSize: '1rem',
                    resize: 'vertical'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleSaveTransaction}
                  style={{ flex: 1 }}
                >
                  <Save size={16} />
                  Guardar transacción
                </button>
                <button
                  className="btn"
                  onClick={() => setShowModal(false)}
                  style={{ flex: 1 }}
                >
                  <X size={16} />
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

