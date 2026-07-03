import { useState, useEffect } from 'react';
import { Wallet, Plus, Edit, Trash2, X, Save } from 'lucide-react';
import { debitCardsApi, participantsApi } from '../services/api';
import { currencySymbol } from '../utils/formatters';

export default function DebitCards() {
  const [cards, setCards] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingCard, setEditingCard] = useState(null);
  const [participantFilter, setParticipantFilter] = useState('all');
  const [cardForm, setCardForm] = useState({
    name: '',
    participant_id: '',
    initial_balance: 0,
    last_four_digits: '',
    active: true,
    currency: 'PEN'
  });

  useEffect(() => {
    fetchDebitCards();
    fetchParticipants();
  }, []);

  const fetchDebitCards = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await debitCardsApi.getAll();
      setCards(data);
    } catch (err) {
      console.error('Error fetching debit cards:', err);
      setError(err.message);
    } finally {
      setLoading(false);
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

  const handleAddCard = () => {
    setCardForm({
      name: '',
      participant_id: participants[0]?.id || '',
      initial_balance: 0,
      last_four_digits: '',
      active: true,
      currency: 'PEN'
    });
    setEditingCard(null);
    setShowModal(true);
  };

  const handleEditCard = (card) => {
    setCardForm({
      name: card.name,
      participant_id: card.participant_id,
      initial_balance: card.initial_balance,
      last_four_digits: card.last_four_digits || '',
      active: card.active,
      currency: card.currency || 'PEN'
    });
    setEditingCard(card);
    setShowModal(true);
  };

  const handleSaveCard = async () => {
    try {
      const payload = {
        name: cardForm.name,
        participant_id: cardForm.participant_id,
        initial_balance: parseFloat(cardForm.initial_balance) || 0,
        active: cardForm.active,
        currency: cardForm.currency
      };

      // Only include last_four_digits if it's not empty
      if (cardForm.last_four_digits && cardForm.last_four_digits.trim() !== '') {
        payload.last_four_digits = cardForm.last_four_digits.trim();
      }

      if (editingCard) {
        await debitCardsApi.update(editingCard.id, payload);
      } else {
        await debitCardsApi.create(payload);
      }

      setShowModal(false);
      setEditingCard(null);
      await fetchDebitCards();
    } catch (err) {
      console.error('Debit card error:', err);
      alert('Error al guardar la tarjeta/cuenta: ' + (err.message || JSON.stringify(err)));
    }
  };

  const handleDeleteCard = async (card) => {
    if (window.confirm(`¿Seguro que quieres eliminar ${card.name}?`)) {
      try {
        await debitCardsApi.delete(card.id);
        await fetchDebitCards();
      } catch (err) {
        alert('Error al eliminar la tarjeta/cuenta: ' + err.message);
      }
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Cargando tarjetas de débito...</p>
        </div>
      </div>
    );
  }

  const filteredCards = cards.filter(card =>
    participantFilter === 'all' || card.participant?.name === participantFilter
  );
  const activeCards = filteredCards.filter(c => c.active);
  const totalBalance = filteredCards.reduce((sum, card) => sum + parseFloat(card.current_balance || 0), 0);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Tarjetas de débito y cuentas bancarias</h1>
          <p className="text-secondary">Controla tu dinero líquido y efectivo disponible</p>
          {error && (
            <div style={{
              marginTop: '0.5rem',
              padding: '0.5rem',
              background: '#FFF3CD',
              border: '1px solid var(--warning)',
              borderRadius: '0.5rem',
              fontSize: '0.85rem'
            }}>
              ⚠️ Error: {error}
            </div>
          )}
        </div>
        <button className="btn btn-primary" onClick={handleAddCard}>
          <Plus size={20} />
          Nueva cuenta
        </button>
      </div>

      {/* Participant Filter */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <label htmlFor="participant-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
          Filtrar por titular de la cuenta
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
            <option key={p.id} value={p.name}>{p.name}</option>
          ))}
        </select>
      </div>

      {/* Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {filteredCards.map(card => {
          const balance = parseFloat(card.current_balance || 0);
          const isNegative = balance < 0;

          return (
            <div
              key={card.id}
              className="card"
              style={{
                background: card.active
                  ? 'linear-gradient(135deg, #569B85, #3E7161)'
                  : 'linear-gradient(135deg, #888, #666)',
                color: 'white',
                opacity: card.active ? 1 : 0.7
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <div>
                  <div style={{ fontSize: '0.875rem', opacity: 0.9, marginBottom: '0.5rem' }}>
                    {card.name}
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 600, letterSpacing: '0.05em' }}>
                    {card.last_four_digits ? `•••• ${card.last_four_digits}` : 'Cuenta en efectivo'}
                  </div>
                </div>
                <Wallet size={32} style={{ opacity: 0.8 }} />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.875rem', opacity: 0.9, marginBottom: '0.25rem' }}>
                  Saldo disponible
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: isNegative ? '#ffcccc' : 'white' }}>
                  {currencySymbol(card.currency)} {balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>

              <div style={{ fontSize: '0.875rem', opacity: 0.9, marginBottom: '1rem' }}>
                Titular: {card.participant?.name || 'Desconocido'}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn"
                  style={{ flex: 1, background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}
                  onClick={() => handleEditCard(card)}
                >
                  <Edit size={16} />
                  Editar
                </button>
                <button
                  className="btn"
                  style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}
                  onClick={() => handleDeleteCard(card)}
                  title="Eliminar"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              {!card.active && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', opacity: 0.7, textAlign: 'center' }}>
                  Inactiva
                </div>
              )}
            </div>
          );
        })}

        {filteredCards.length === 0 && (
          <div className="card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }}>
            <Wallet size={64} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
            <h3 style={{ marginBottom: '0.5rem' }}>Aún no hay tarjetas de débito</h3>
            <p className="text-secondary">Crea tu primera cuenta bancaria o tarjeta de débito para controlar tu dinero líquido</p>
            <button className="btn btn-primary" onClick={handleAddCard} style={{ marginTop: '1rem' }}>
              <Plus size={20} />
              Agregar cuenta
            </button>
          </div>
        )}
      </div>

      {/* Summary Statistics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ background: 'var(--primary)', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Total de cuentas</p>
          <h2 style={{ margin: 0 }}>{filteredCards.length}</h2>
        </div>
        <div className="card" style={{ background: 'var(--secondary)', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Cuentas activas</p>
          <h2 style={{ margin: 0 }}>{activeCards.length}</h2>
        </div>
        <div className="card" style={{ background: totalBalance >= 0 ? '#569B85' : '#c66666', color: 'white' }}>
          <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Efectivo disponible total</p>
          <h2 style={{ margin: 0 }}>
            S/ {totalBalance.toLocaleString()}
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
              <h2 style={{ margin: 0 }}>{editingCard ? 'Editar cuenta' : 'Nueva cuenta'}</h2>
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
                  Nombre de la cuenta *
                </label>
                <input
                  type="text"
                  value={cardForm.name}
                  onChange={(e) => setCardForm({ ...cardForm, name: e.target.value })}
                  placeholder="Ej.: Cuenta corriente, Ahorros"
                  className="input"
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Titular *
                </label>
                <select
                  value={cardForm.participant_id}
                  onChange={(e) => setCardForm({ ...cardForm, participant_id: e.target.value })}
                  className="input"
                >
                  <option value="">Seleccionar titular</option>
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
                  className="input"
                >
                  <option value="PEN">PEN — Soles</option>
                  <option value="USD">USD — Dólares</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Saldo inicial
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={cardForm.initial_balance}
                  onChange={(e) => setCardForm({ ...cardForm, initial_balance: e.target.value })}
                  className="input"
                />
                <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
                  Saldo de inicio de esta cuenta
                </small>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Últimos 4 dígitos (opcional)
                </label>
                <input
                  type="text"
                  maxLength="4"
                  value={cardForm.last_four_digits}
                  onChange={(e) => setCardForm({ ...cardForm, last_four_digits: e.target.value })}
                  placeholder="1234"
                  className="input"
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="active"
                  checked={cardForm.active}
                  onChange={(e) => setCardForm({ ...cardForm, active: e.target.checked })}
                />
                <label htmlFor="active">Activa</label>
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
    </div>
  );
}

