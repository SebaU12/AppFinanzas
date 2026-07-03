import { useState, useEffect } from 'react';
import { CreditCard as CreditCardIcon, Plus, Edit, Trash2, Calendar, DollarSign, X, Save, Check, Square, CheckSquare } from 'lucide-react';
import { creditCardsApi, installmentsApi, participantsApi } from '../services/api';
import { getCurrentMonth, formatLocalDate, currencySymbol } from '../utils/formatters';

export default function CreditCards() {
  const [cards, setCards] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [installments, setInstallments] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingCard, setEditingCard] = useState(null);
  const [installmentFilter, setInstallmentFilter] = useState('active'); // 'active', 'historical', 'all'
  const [participantFilter, setParticipantFilter] = useState('all'); // Filter cards by participant
  const [selectedInstallments, setSelectedInstallments] = useState(new Set());
  const [debitCards, setDebitCards] = useState([]);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentForm, setPaymentForm] = useState({ debit_card_id: '', paid_date: new Date().toISOString().split('T')[0] });
  const [pendingPayment, setPendingPayment] = useState(null); // { type: 'single'|'bulk', installment?, ids? }
  const [cardForm, setCardForm] = useState({
    name: '',
    participant_id: '',
    closing_day: 15,
    payment_day: 5,
    credit_limit: 5000,
    currency: 'PEN'
  });

  useEffect(() => {
    fetchCreditCards();
    fetchParticipants();
    fetchDebitCards();
  }, []);

  useEffect(() => {
    if (selectedCard) {
      fetchInstallments(selectedCard.id);
      setSelectedInstallments(new Set());
    }
  }, [selectedCard]);

  // Reset selected card when participant filter changes
  useEffect(() => {
    const filteredCards = cards.filter(card =>
      participantFilter === 'all' || card.owner === participantFilter
    );

    // If current selected card is not in filtered list, select first filtered card
    if (selectedCard && !filteredCards.find(c => c.id === selectedCard.id)) {
      if (filteredCards.length > 0) {
        setSelectedCard(filteredCards[0]);
      } else {
        setSelectedCard(null);
      }
    } else if (!selectedCard && filteredCards.length > 0) {
      // If no card is selected, select the first one
      setSelectedCard(filteredCards[0]);
    }
  }, [participantFilter, cards]);

  const fetchCreditCards = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await creditCardsApi.getAll();

      // Fetch ALL installments to calculate balances (not just current month)
      const allInstallments = await installmentsApi.getAll().catch(() => []);

      // Map API response with calculated balances
      const mappedCards = data.map(card => {
        // Calculate current balance from installments for this card
        const cardInstallments = allInstallments.filter(inst => inst.credit_card_id === card.id);
        const totalBalance = cardInstallments.reduce((sum, inst) => sum + parseFloat(inst.amount || 0), 0);
        const unpaidBalance = cardInstallments
          .filter(inst => !inst.paid)
          .reduce((sum, inst) => sum + parseFloat(inst.amount || 0), 0);
        const paidBalance = cardInstallments
          .filter(inst => inst.paid)
          .reduce((sum, inst) => sum + parseFloat(inst.amount || 0), 0);
        const creditLimit = card.credit_limit || 5000;
        // Available credit = limit - unpaid balance (not total balance)
        // When you pay an installment, you get that credit back
        const availableCredit = creditLimit - unpaidBalance;

        return {
          id: card.id,
          name: card.name,
          participant_id: card.participant_id,
          lastFourDigits: card.last_four_digits || '****',
          owner: card.participant?.name || 'Desconocido',
          closingDay: card.closing_day,
          paymentDay: card.payment_day,
          creditLimit: creditLimit,
          currentBalance: totalBalance,
          unpaidBalance: unpaidBalance,
          paidBalance: paidBalance,
          availableCredit: availableCredit,
          currency: card.currency || 'PEN'
        };
      });

      setCards(mappedCards);

      if (mappedCards.length > 0 && !selectedCard) {
        setSelectedCard(mappedCards[0]);
      }
    } catch (err) {
      console.error('Error fetching credit cards:', err);
      setError(err.message);
      // Fallback to mock data
      setCards([
        {
          id: 1,
          name: 'Visa Banco Nacional',
          lastFourDigits: '4532',
          owner: 'Lu',
          closingDay: 15,
          paymentDay: 5,
          currentBalance: 1250.50,
          availableCredit: 3749.50,
          creditLimit: 5000
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchInstallments = async (cardId) => {
    try {
      // Fetch ALL installments for the card, not just current month
      const allInstallments = await installmentsApi.getAll();

      // Filter installments for the selected card
      const cardInstallments = allInstallments
        .filter(inst => inst.credit_card_id === cardId)
        .map(inst => {
          const transaction = inst.transaction || {};
          const totalInstallments = transaction.installment_count || 1;
          const totalAmount = parseFloat(transaction.amount || 0);
          const monthlyAmount = parseFloat(inst.amount || 0);
          const installmentNumber = inst.installment_number || 1;

          // Calculate remaining amount: (total installments - current installment) * monthly amount
          const remainingInstallments = totalInstallments - installmentNumber;
          const remainingAmount = remainingInstallments * monthlyAmount;

          // Parse month to create due date using the card's payment day
          const [year, month] = inst.month.split('-');
          const paymentDay = selectedCard?.paymentDay || 1;
          const dueDate = new Date(parseInt(year), parseInt(month) - 1, paymentDay);

          return {
            id: inst.id,
            description: transaction.description || 'Desconocido',
            purchaseDate: transaction.date || null,
            totalAmount: totalAmount,
            installmentNumber: installmentNumber,
            totalInstallments: totalInstallments,
            monthlyAmount: monthlyAmount,
            remainingAmount: remainingAmount,
            dueDate: dueDate,
            paid: inst.paid || false
          };
        });

      setInstallments(cardInstallments);
    } catch (err) {
      console.error('Error fetching installments:', err);
      // No fallback data - show empty state
      setInstallments([]);
    }
  };

  const fetchParticipants = async () => {
    try {
      const data = await participantsApi.getAll();
      setParticipants(data);
    } catch (err) {
      console.error('Error fetching participants:', err);
    }
  };

  const fetchDebitCards = async () => {
    try {
      const { debitCardsApi } = await import('../services/api');
      const data = await debitCardsApi.getAll();
      setDebitCards(data);
    } catch (err) {
      console.error('Error fetching debit cards:', err);
    }
  };

  const handleAddCard = () => {
    setCardForm({
      name: '',
      participant_id: participants[0]?.id || '',
      closing_day: 15,
      payment_day: 5,
      credit_limit: 5000,
      currency: 'PEN'
    });
    setEditingCard(null);
    setShowModal(true);
  };

  const handleEditCard = (card) => {
    setCardForm({
      name: card.name,
      participant_id: card.participant_id || participants[0]?.id || '',
      closing_day: card.closingDay,
      payment_day: card.paymentDay,
      credit_limit: card.creditLimit || 5000,
      currency: card.currency || 'PEN'
    });
    setEditingCard(card);
    setShowModal(true);
  };

  const handleSaveCard = async () => {
    try {
      if (editingCard) {
        await creditCardsApi.update(editingCard.id, cardForm);
      } else {
        await creditCardsApi.create(cardForm);
      }
      setShowModal(false);
      setEditingCard(null);
      await fetchCreditCards();
    } catch (err) {
      alert('Error al guardar la tarjeta de crédito: ' + err.message);
    }
  };

  const handleDeleteCard = async (card) => {
    if (window.confirm(`¿Seguro que quieres eliminar ${card.name}? Esto puede afectar transacciones existentes.`)) {
      try {
        await creditCardsApi.delete(card.id);
        await fetchCreditCards();
      } catch (err) {
        alert('Error al eliminar la tarjeta de crédito: ' + err.message);
      }
    }
  };

  const handleToggleInstallmentPaid = async (installment) => {
    if (!installment.paid) {
      // Marking as paid: open payment modal
      setPendingPayment({ type: 'single', installment });
      setPaymentForm({ debit_card_id: debitCards[0]?.id || '', paid_date: new Date().toISOString().split('T')[0] });
      setShowPaymentModal(true);
    } else {
      // Unmarking: no debit card needed
      try {
        await installmentsApi.markPaid(installment.id, false);
        if (selectedCard) {
          await fetchInstallments(selectedCard.id);
          await fetchCreditCards();
        }
      } catch (err) {
        alert('Error al actualizar la cuota: ' + err.message);
      }
    }
  };

  const handleConfirmPayment = async () => {
    try {
      const { debit_card_id, paid_date } = paymentForm;
      if (pendingPayment.type === 'single') {
        await installmentsApi.markPaid(pendingPayment.installment.id, true, debit_card_id || null, paid_date || null);
      } else {
        const ids = [...selectedInstallments];
        await installmentsApi.bulkMarkPaid(ids, true, debit_card_id || null, paid_date || null);
        setSelectedInstallments(new Set());
      }
      setShowPaymentModal(false);
      setPendingPayment(null);
      if (selectedCard) {
        await fetchInstallments(selectedCard.id);
        await fetchCreditCards();
      }
    } catch (err) {
      alert('Error al registrar el pago: ' + err.message);
    }
  };

  const handleToggleSelectInstallment = (id) => {
    setSelectedInstallments(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleSelectAll = (visibleInstallments) => {
    const allIds = visibleInstallments.map(i => i.id);
    const allSelected = allIds.every(id => selectedInstallments.has(id));
    if (allSelected) {
      setSelectedInstallments(new Set());
    } else {
      setSelectedInstallments(new Set(allIds));
    }
  };

  const handleBulkMarkPaid = () => {
    if (selectedInstallments.size === 0) return;
    setPendingPayment({ type: 'bulk' });
    setPaymentForm({ debit_card_id: debitCards[0]?.id || '', paid_date: new Date().toISOString().split('T')[0] });
    setShowPaymentModal(true);
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Cargando tarjetas de crédito...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Tarjetas de crédito</h1>
          <p className="text-secondary">Gestiona tarjetas de crédito y cuotas</p>
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
        <button className="btn btn-primary" onClick={handleAddCard}>
          <Plus size={20} />
          Nueva tarjeta
        </button>
      </div>

      {/* Participant Filter */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <label htmlFor="participant-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
          Filtrar por titular de la tarjeta
        </label>
        <select
          id="participant-filter"
          className="input"
          value={participantFilter}
          onChange={(e) => setParticipantFilter(e.target.value)}
          style={{ maxWidth: '300px' }}
        >
          <option value="all">Todos los participantes</option>
          {participants.map((p) => (
            <option key={p.id} value={p.name}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {/* Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {cards.filter(card =>
          participantFilter === 'all' || card.owner === participantFilter
        ).map(card => {
          // Usage percentage based on UNPAID balance (actual credit being used)
          const usagePercentage = card.creditLimit > 0 ? ((card.unpaidBalance / card.creditLimit) * 100).toFixed(1) : 0;

          return (
            <div
              key={card.id}
              className="card"
              style={{
                background: `linear-gradient(135deg, var(--primary), var(--primary-dark))`,
                color: 'white',
                cursor: 'pointer',
                border: selectedCard?.id === card.id ? '3px solid var(--secondary)' : 'none'
              }}
              onClick={() => setSelectedCard(card)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <div>
                  <div style={{ fontSize: '0.875rem', opacity: 0.9, marginBottom: '0.5rem' }}>
                    {card.name}
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '0.1em' }}>
                    •••• {card.lastFourDigits}
                  </div>
                </div>
                <CreditCardIcon size={32} style={{ opacity: 0.8 }} />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.875rem', opacity: 0.9, marginBottom: '0.25rem' }}>
                  Crédito disponible
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>
                  {currencySymbol(card.currency)} {card.availableCredit.toLocaleString()}
                </div>
                <div style={{ fontSize: '0.875rem', opacity: 0.9, marginTop: '0.25rem' }}>
                  de {currencySymbol(card.currency)} {card.creditLimit.toLocaleString()} ({(100 - parseFloat(usagePercentage)).toFixed(1)}% disponible)
                </div>
                <div style={{ fontSize: '0.875rem', opacity: 0.9, marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.2)' }}>
                  Pendiente: {currencySymbol(card.currency)} {card.unpaidBalance.toLocaleString()} | Pagado: {currencySymbol(card.currency)} {card.paidBalance.toLocaleString()}
                </div>
              </div>

              {/* Usage bar */}
              <div style={{ background: 'rgba(255,255,255,0.2)', height: '6px', borderRadius: '3px', overflow: 'hidden', marginBottom: '1rem' }}>
                <div
                  style={{
                    background: parseFloat(usagePercentage) > 80 ? 'var(--accent)' : 'white',
                    height: '100%',
                    width: `${usagePercentage}%`,
                    transition: 'width 0.3s ease'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', opacity: 0.9 }}>
                <div>
                  <Calendar size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                  Cierre: día {card.closingDay}
                </div>
                <div>
                  <DollarSign size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                  Pago: día {card.paymentDay}
                </div>
              </div>

              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.2)' }}>
                <div style={{ fontSize: '0.875rem', opacity: 0.9 }}>Titular: {card.owner}</div>
              </div>

              <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn"
                  style={{ flex: 1, background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleEditCard(card);
                  }}
                >
                  <Edit size={16} />
                  Editar
                </button>
                <button
                  className="btn"
                  style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCard(card);
                  }}
                  title="Eliminar"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Installments Section */}
      {selectedCard && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>
              Cuotas - {selectedCard.name}
            </h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className={`btn ${installmentFilter === 'active' ? 'btn-primary' : ''}`}
                onClick={() => setInstallmentFilter('active')}
                style={{ padding: '0.5rem 1rem' }}
              >
                Activas
              </button>
              <button
                className={`btn ${installmentFilter === 'historical' ? 'btn-primary' : ''}`}
                onClick={() => setInstallmentFilter('historical')}
                style={{ padding: '0.5rem 1rem' }}
              >
                Históricas
              </button>
              <button
                className={`btn ${installmentFilter === 'all' ? 'btn-primary' : ''}`}
                onClick={() => setInstallmentFilter('all')}
                style={{ padding: '0.5rem 1rem' }}
              >
                Todas
              </button>
            </div>
          </div>

          {(() => {
            const visibleInstallments = installments.filter(inst => {
              if (installmentFilter === 'active') return !inst.paid;
              if (installmentFilter === 'historical') return inst.paid;
              return true;
            });
            const allSelected = visibleInstallments.length > 0 && visibleInstallments.every(i => selectedInstallments.has(i.id));
            const someSelected = selectedInstallments.size > 0;

            if (visibleInstallments.length === 0) {
              return (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                  No hay cuotas {installmentFilter === 'active' ? 'activas' : installmentFilter === 'historical' ? 'históricas' : ''} para esta tarjeta
                </div>
              );
            }

            return (
              <>
                {someSelected && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', padding: '0.75rem 1rem', background: 'var(--primary-light, #e8f0fe)', borderRadius: '0.5rem' }}>
                    <span style={{ fontWeight: 600 }}>{selectedInstallments.size} cuota(s) seleccionada(s)</span>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleBulkMarkPaid(visibleInstallments)}
                      style={{ padding: '0.4rem 1rem' }}
                    >
                      <Check size={16} />
                      Confirmar pago
                    </button>
                    <button
                      className="btn"
                      onClick={() => setSelectedInstallments(new Set())}
                      style={{ padding: '0.4rem 1rem' }}
                    >
                      <X size={16} />
                      Cancelar
                    </button>
                  </div>
                )}
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--primary)' }}>
                        <th style={{ textAlign: 'center', padding: '1rem', width: '48px' }}>
                          <button
                            onClick={() => handleSelectAll(visibleInstallments)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: allSelected ? 'var(--primary)' : '#999' }}
                            title={allSelected ? 'Deseleccionar todo' : 'Seleccionar todo'}
                          >
                            {allSelected ? <CheckSquare size={20} /> : <Square size={20} />}
                          </button>
                        </th>
                        <th style={{ textAlign: 'center', padding: '1rem', width: '60px' }}>Pagada</th>
                        <th style={{ textAlign: 'left', padding: '1rem' }}>Descripción</th>
                        <th style={{ textAlign: 'center', padding: '1rem' }}>Fecha compra</th>
                        <th style={{ textAlign: 'center', padding: '1rem' }}>Progreso</th>
                        <th style={{ textAlign: 'right', padding: '1rem' }}>Mensual</th>
                        <th style={{ textAlign: 'right', padding: '1rem' }}>Total</th>
                        <th style={{ textAlign: 'right', padding: '1rem' }}>Restante</th>
                        <th style={{ textAlign: 'center', padding: '1rem' }}>Próximo vencimiento</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleInstallments.map(inst => {
                        const progress = ((inst.installmentNumber / inst.totalInstallments) * 100).toFixed(0);
                        const isSelected = selectedInstallments.has(inst.id);

                        return (
                          <tr
                            key={inst.id}
                            style={{
                              borderBottom: '1px solid #e0e0e0',
                              opacity: inst.paid ? 0.6 : 1,
                              background: isSelected ? 'var(--primary-light, #e8f0fe)' : inst.paid ? '#f5f5f5' : 'transparent',
                              cursor: 'pointer'
                            }}
                            onClick={() => !inst.paid && handleToggleSelectInstallment(inst.id)}
                          >
                            <td style={{ padding: '1rem', textAlign: 'center' }} onClick={e => e.stopPropagation()}>
                              {!inst.paid && (
                                <button
                                  onClick={() => handleToggleSelectInstallment(inst.id)}
                                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: isSelected ? 'var(--primary)' : '#999' }}
                                >
                                  {isSelected ? <CheckSquare size={20} /> : <Square size={20} />}
                                </button>
                              )}
                            </td>
                            <td style={{ padding: '1rem', textAlign: 'center' }} onClick={e => e.stopPropagation()}>
                              <button
                                onClick={() => handleToggleInstallmentPaid(inst)}
                                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: inst.paid ? 'var(--primary)' : '#999' }}
                                title={inst.paid ? 'Marcar como no pagada' : 'Marcar como pagada'}
                              >
                                {inst.paid ? <CheckSquare size={24} /> : <Square size={24} />}
                              </button>
                            </td>
                            <td style={{ padding: '1rem', fontWeight: 600 }}>
                              {inst.description}
                              {inst.paid && (
                                <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 'normal' }}>
                                  (Pagada)
                                </span>
                              )}
                            </td>
                            <td style={{ padding: '1rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                              {inst.purchaseDate
                                ? new Date(inst.purchaseDate + 'T00:00:00').toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' })
                                : '—'}
                            </td>
                            <td style={{ padding: '1rem' }}>
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                                <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                                  {inst.installmentNumber} / {inst.totalInstallments}
                                </div>
                                <div style={{ width: '100%', maxWidth: '100px', background: '#e0e0e0', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                                  <div style={{ background: 'var(--primary)', height: '100%', width: `${progress}%` }} />
                                </div>
                              </div>
                            </td>
                            <td style={{ padding: '1rem', textAlign: 'right', fontWeight: 600 }}>
                              {currencySymbol(selectedCard?.currency)} {inst.monthlyAmount.toLocaleString()}
                            </td>
                            <td style={{ padding: '1rem', textAlign: 'right' }}>
                              {currencySymbol(selectedCard?.currency)} {inst.totalAmount.toLocaleString()}
                            </td>
                            <td style={{ padding: '1rem', textAlign: 'right', color: 'var(--accent)', fontWeight: 600 }}>
                              {currencySymbol(selectedCard?.currency)} {inst.remainingAmount.toLocaleString()}
                            </td>
                            <td style={{ padding: '1rem', textAlign: 'center' }}>
                              {new Date(inst.dueDate).toLocaleDateString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            );
          })()}
        </div>
      )}

      {/* Summary Statistics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
        <div className="card" style={{ background: 'var(--primary)', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Total de tarjetas</p>
          <h2 style={{ margin: 0 }}>
            {cards.filter(c => participantFilter === 'all' || c.owner === participantFilter).length}
          </h2>
        </div>
        <div className="card" style={{ background: '#c66666', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Saldo pendiente</p>
          <h2 style={{ margin: 0 }}>
            S/ {cards.filter(c => participantFilter === 'all' || c.owner === participantFilter).reduce((sum, c) => sum + (c.unpaidBalance || 0), 0).toLocaleString()}
          </h2>
        </div>
        <div className="card" style={{ background: 'var(--secondary)', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Crédito disponible</p>
          <h2 style={{ margin: 0 }}>
            S/ {cards.filter(c => participantFilter === 'all' || c.owner === participantFilter).reduce((sum, c) => sum + (c.availableCredit || 0), 0).toLocaleString()}
          </h2>
        </div>
      </div>

      {/* Modal for Add/Edit Card */}
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
              maxWidth: '500px',
              width: '90%',
              maxHeight: '90vh',
              overflow: 'auto'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>{editingCard ? 'Editar tarjeta de crédito' : 'Nueva tarjeta de crédito'}</h2>
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
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Nombre de la tarjeta *
                </label>
                <input
                  type="text"
                  value={cardForm.name}
                  onChange={(e) => setCardForm({ ...cardForm, name: e.target.value })}
                  placeholder="Ej.: Visa Platinum"
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
                  Titular (participante) *
                </label>
                <select
                  value={cardForm.participant_id}
                  onChange={(e) => setCardForm({ ...cardForm, participant_id: e.target.value })}
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
                  Moneda *
                </label>
                <select
                  value={cardForm.currency}
                  onChange={(e) => setCardForm({ ...cardForm, currency: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '0.5rem',
                    fontSize: '1rem'
                  }}
                >
                  <option value="PEN">PEN — Soles</option>
                  <option value="USD">USD — Dólares</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Límite de crédito *
                </label>
                <input
                  type="number"
                  min="0"
                  step="100"
                  value={cardForm.credit_limit}
                  onChange={(e) => setCardForm({ ...cardForm, credit_limit: parseInt(e.target.value) })}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '0.5rem',
                    fontSize: '1rem'
                  }}
                />
                <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
                  Crédito máximo disponible en esta tarjeta
                </small>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Día de cierre *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={cardForm.closing_day}
                    onChange={(e) => setCardForm({ ...cardForm, closing_day: parseInt(e.target.value) })}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '0.5rem',
                      fontSize: '1rem'
                    }}
                  />
                  <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
                    Día del mes (1-31)
                  </small>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Día de pago *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={cardForm.payment_day}
                    onChange={(e) => setCardForm({ ...cardForm, payment_day: parseInt(e.target.value) })}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '0.5rem',
                      fontSize: '1rem'
                    }}
                  />
                  <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
                    Día del mes (1-31)
                  </small>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleSaveCard}
                  style={{ flex: 1 }}
                >
                  <Save size={16} />
                  Guardar
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

      {/* Modal de pago de cuota — transferencia desde débito */}
      {showPaymentModal && (
        <div
          style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
          onClick={() => setShowPaymentModal(false)}
        >
          <div
            className="card"
            style={{ maxWidth: '420px', width: '90%' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ margin: 0 }}>Registrar pago al banco</h3>
              <button onClick={() => setShowPaymentModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Este pago es una <strong>transferencia</strong> de tu cuenta de débito a la tarjeta de crédito.
              No cuenta como gasto nuevo — el gasto ya fue registrado cuando hiciste la compra.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Cuenta de débito origen
                </label>
                <select
                  className="input"
                  value={paymentForm.debit_card_id}
                  onChange={(e) => setPaymentForm({ ...paymentForm, debit_card_id: e.target.value })}
                  style={{ width: '100%' }}
                >
                  <option value="">Sin registrar (solo marcar pagada)</option>
                  {debitCards.map(dc => (
                    <option key={dc.id} value={dc.id}>
                      {dc.name} {dc.participant?.name ? `(${dc.participant.name})` : ''} — Saldo: {currencySymbol(dc.currency)} {parseFloat(dc.current_balance || 0).toLocaleString()}
                    </option>
                  ))}
                </select>
                <small style={{ color: 'var(--text-secondary)', display: 'block', marginTop: '0.25rem' }}>
                  Si seleccionas una cuenta, su saldo se reducirá por el monto de la(s) cuota(s).
                </small>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Fecha del pago
                </label>
                <input
                  type="date"
                  className="input"
                  value={paymentForm.paid_date}
                  onChange={(e) => setPaymentForm({ ...paymentForm, paid_date: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <button className="btn btn-primary" onClick={handleConfirmPayment} style={{ flex: 1 }}>
                  <Check size={16} />
                  Confirmar pago
                </button>
                <button className="btn" onClick={() => setShowPaymentModal(false)} style={{ flex: 1 }}>
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

