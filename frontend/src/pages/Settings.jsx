import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Users, Tag, CreditCard, Plus, Edit2, Trash2, Save, X } from 'lucide-react';
import './Settings.css';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('participants');
  const [participants, setParticipants] = useState([]);
  const [categories, setCategories] = useState([]);
  const [creditCards, setCreditCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form states
  const [editingParticipant, setEditingParticipant] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingCreditCard, setEditingCreditCard] = useState(null);
  const [showParticipantForm, setShowParticipantForm] = useState(false);
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [showCreditCardForm, setShowCreditCardForm] = useState(false);

  const [participantForm, setParticipantForm] = useState({
    name: '',
    default_percentage: 50
  });

  const [categoryForm, setCategoryForm] = useState({
    name: '',
    type: 'expense',
    is_personal: false,
    allows_credit: true,
    parent_id: null
  });

  const [creditCardForm, setCreditCardForm] = useState({
    name: '',
    participant_id: '',
    closing_day: 15,
    payment_day: 5,
    currency: 'PEN'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [participantsData, categoriesData, creditCardsData] = await Promise.all([
        api.getParticipants(),
        api.getCategories(),
        api.getCreditCards()
      ]);
      setParticipants(participantsData);
      setCategories(categoriesData);
      setCreditCards(creditCardsData);
    } catch (err) {
      setError('Error al cargar los datos de configuración');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Participant handlers
  const handleAddParticipant = () => {
    setParticipantForm({ name: '', default_percentage: 50 });
    setEditingParticipant(null);
    setShowParticipantForm(true);
  };

  const handleEditParticipant = (participant) => {
    setParticipantForm({
      name: participant.name,
      default_percentage: participant.default_percentage
    });
    setEditingParticipant(participant);
    setShowParticipantForm(true);
  };

  const handleSaveParticipant = async () => {
    try {
      if (editingParticipant) {
        await api.updateParticipant(editingParticipant.id, participantForm);
      } else {
        await api.createParticipant(participantForm);
      }
      await loadData();
      setShowParticipantForm(false);
      setEditingParticipant(null);
    } catch (err) {
      alert('Error al guardar el participante: ' + err.message);
    }
  };

  const handleDeleteParticipant = async (id) => {
    if (window.confirm('¿Seguro que quieres eliminar este participante? Esta acción no se puede deshacer.')) {
      try {
        await api.deleteParticipant(id);
        await loadData();
      } catch (err) {
        alert('Error al eliminar el participante: ' + err.message);
      }
    }
  };

  // Category handlers
  const handleAddCategory = (parentId = null) => {
    setCategoryForm({
      name: '',
      type: 'expense',
      is_personal: false,
      allows_credit: true,
      parent_id: parentId
    });
    setEditingCategory(null);
    setShowCategoryForm(true);
  };

  const handleEditCategory = (category) => {
    setCategoryForm({
      name: category.name,
      type: category.type,
      is_personal: category.is_personal,
      allows_credit: category.allows_credit,
      parent_id: category.parent_id || null
    });
    setEditingCategory(category);
    setShowCategoryForm(true);
  };

  const handleSaveCategory = async () => {
    try {
      if (editingCategory) {
        await api.updateCategory(editingCategory.id, categoryForm);
      } else {
        await api.createCategory(categoryForm);
      }
      await loadData();
      setShowCategoryForm(false);
      setEditingCategory(null);
    } catch (err) {
      alert('Error al guardar la categoría: ' + err.message);
    }
  };

  const handleDeleteCategory = async (id) => {
    if (window.confirm('¿Seguro que quieres eliminar esta categoría? Esto puede afectar transacciones existentes.')) {
      try {
        await api.deleteCategory(id);
        await loadData();
      } catch (err) {
        alert('Error al eliminar la categoría: ' + err.message);
      }
    }
  };

  // Credit Card handlers
  const handleAddCreditCard = () => {
    setCreditCardForm({
      name: '',
      participant_id: participants[0]?.id || '',
      closing_day: 15,
      payment_day: 5,
      currency: 'PEN'
    });
    setEditingCreditCard(null);
    setShowCreditCardForm(true);
  };

  const handleEditCreditCard = (card) => {
    setCreditCardForm({
      name: card.name,
      participant_id: card.participant_id,
      closing_day: card.closing_day,
      payment_day: card.payment_day,
      currency: card.currency || 'PEN'
    });
    setEditingCreditCard(card);
    setShowCreditCardForm(true);
  };

  const handleSaveCreditCard = async () => {
    try {
      if (editingCreditCard) {
        await api.updateCreditCard(editingCreditCard.id, creditCardForm);
      } else {
        await api.createCreditCard(creditCardForm);
      }
      await loadData();
      setShowCreditCardForm(false);
      setEditingCreditCard(null);
    } catch (err) {
      alert('Error al guardar la tarjeta de crédito: ' + err.message);
    }
  };

  const handleDeleteCreditCard = async (id) => {
    if (window.confirm('¿Seguro que quieres eliminar esta tarjeta de crédito? Esto puede afectar transacciones existentes.')) {
      try {
        await api.deleteCreditCard(id);
        await loadData();
      } catch (err) {
        alert('Error al eliminar la tarjeta de crédito: ' + err.message);
      }
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Cargando configuración...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-state">{error}</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Configuración</h1>
        <p>Administra participantes, categorías y la configuración de la aplicación</p>
      </div>

      <div className="settings-tabs">
        <button
          className={`tab-button ${activeTab === 'participants' ? 'active' : ''}`}
          onClick={() => setActiveTab('participants')}
        >
          <Users size={20} />
          Participantes
        </button>
        <button
          className={`tab-button ${activeTab === 'categories' ? 'active' : ''}`}
          onClick={() => setActiveTab('categories')}
        >
          <Tag size={20} />
          Categorías
        </button>
        <button
          className={`tab-button ${activeTab === 'creditCards' ? 'active' : ''}`}
          onClick={() => setActiveTab('creditCards')}
        >
          <CreditCard size={20} />
          Tarjetas de crédito
        </button>
      </div>

      {activeTab === 'participants' && (
        <div className="settings-section">
          <div className="section-header">
            <h2>Participantes</h2>
            <button className="btn-primary" onClick={handleAddParticipant}>
              <Plus size={16} />
              Agregar participante
            </button>
          </div>

          {showParticipantForm && (
            <div className="form-card">
              <h3>{editingParticipant ? 'Editar participante' : 'Nuevo participante'}</h3>
              <div className="form-group">
                <label>Nombre *</label>
                <input
                  type="text"
                  value={participantForm.name}
                  onChange={(e) => setParticipantForm({ ...participantForm, name: e.target.value })}
                  placeholder="Ingresa el nombre del participante"
                />
              </div>
              <div className="form-group">
                <label>% de reembolso por defecto *</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={participantForm.default_percentage}
                  onChange={(e) => setParticipantForm({
                    ...participantForm,
                    default_percentage: parseFloat(e.target.value)
                  })}
                />
                <small>Porcentaje que este participante paga en gastos compartidos (0-100)</small>
              </div>
              <div className="form-actions">
                <button className="btn-primary" onClick={handleSaveParticipant}>
                  <Save size={16} />
                  Guardar
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setShowParticipantForm(false);
                    setEditingParticipant(null);
                  }}
                >
                  <X size={16} />
                  Cancelar
                </button>
              </div>
            </div>
          )}

          <div className="settings-list">
            {participants.map((participant) => (
              <div key={participant.id} className="settings-item">
                <div className="item-info">
                  <h3>{participant.name}</h3>
                  <p>Reembolso por defecto: {participant.default_percentage}%</p>
                </div>
                <div className="item-actions">
                  <button
                    className="btn-icon"
                    onClick={() => handleEditParticipant(participant)}
                    title="Editar"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    className="btn-icon btn-danger"
                    onClick={() => handleDeleteParticipant(participant.id)}
                    title="Eliminar"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'categories' && (
        <div className="settings-section">
          <div className="section-header">
            <h2>Categorías</h2>
            <button className="btn-primary" onClick={() => handleAddCategory(null)}>
              <Plus size={16} />
              Agregar categoría
            </button>
          </div>

          {showCategoryForm && (
            <div className="form-card">
              <h3>
                {editingCategory ? 'Editar categoría' : categoryForm.parent_id ? 'Nueva subcategoría' : 'Nueva categoría'}
              </h3>
              <div className="form-group">
                <label>Nombre *</label>
                <input
                  type="text"
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                  placeholder="Ingresa el nombre de la categoría"
                />
              </div>
              <div className="form-group">
                <label>Categoría padre (opcional)</label>
                <select
                  value={categoryForm.parent_id || ''}
                  onChange={(e) => setCategoryForm({ ...categoryForm, parent_id: e.target.value || null })}
                >
                  <option value="">Sin padre (categoría raíz)</option>
                  {categories
                    .filter(c => !c.parent_id && (!editingCategory || c.id !== editingCategory.id))
                    .map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))
                  }
                </select>
              </div>
              <div className="form-group">
                <label>Tipo *</label>
                <select
                  value={categoryForm.type}
                  onChange={(e) => setCategoryForm({ ...categoryForm, type: e.target.value })}
                >
                  <option value="income">Ingreso</option>
                  <option value="expense">Gasto</option>
                </select>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={categoryForm.is_personal}
                    onChange={(e) => setCategoryForm({ ...categoryForm, is_personal: e.target.checked })}
                  />
                  Personal (excluir de reembolsos)
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={categoryForm.allows_credit}
                    onChange={(e) => setCategoryForm({ ...categoryForm, allows_credit: e.target.checked })}
                  />
                  Permitir pagos con tarjeta de crédito
                </label>
              </div>
              <div className="form-actions">
                <button className="btn-primary" onClick={handleSaveCategory}>
                  <Save size={16} />
                  Guardar
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setShowCategoryForm(false);
                    setEditingCategory(null);
                  }}
                >
                  <X size={16} />
                  Cancelar
                </button>
              </div>
            </div>
          )}

          <div className="settings-list">
            {/* Categorías raíz y sus subcategorías agrupadas */}
            {categories
              .filter(c => !c.parent_id)
              .map(parent => {
                const subcategories = categories.filter(c => c.parent_id === parent.id);
                return (
                  <React.Fragment key={parent.id}>
                    {/* Categoría padre */}
                    <div className="settings-item category-parent">
                      <div className="item-info">
                        <h3>{parent.name}</h3>
                        <div className="category-badges">
                          <span className={`badge ${parent.type === 'income' ? 'badge-success' : 'badge-danger'}`}>
                            {parent.type === 'income' ? 'Ingreso' : 'Gasto'}
                          </span>
                          {parent.is_personal && <span className="badge badge-warning">Personal</span>}
                          {parent.allows_credit && <span className="badge badge-info">Crédito OK</span>}
                        </div>
                      </div>
                      <div className="item-actions">
                        <button
                          className="btn-icon"
                          onClick={() => handleAddCategory(parent.id)}
                          title="Agregar subcategoría"
                        >
                          <Plus size={16} />
                        </button>
                        <button
                          className="btn-icon"
                          onClick={() => handleEditCategory(parent)}
                          title="Editar"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          className="btn-icon btn-danger"
                          onClick={() => handleDeleteCategory(parent.id)}
                          title="Eliminar"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                    {/* Subcategorías */}
                    {subcategories.map(sub => (
                      <div key={sub.id} className="settings-item category-child">
                        <div className="item-info">
                          <h3>↳ {sub.name}</h3>
                          <div className="category-badges">
                            <span className={`badge ${sub.type === 'income' ? 'badge-success' : 'badge-danger'}`}>
                              {sub.type === 'income' ? 'Ingreso' : 'Gasto'}
                            </span>
                            {sub.is_personal && <span className="badge badge-warning">Personal</span>}
                            {sub.allows_credit && <span className="badge badge-info">Crédito OK</span>}
                          </div>
                        </div>
                        <div className="item-actions">
                          <button
                            className="btn-icon"
                            onClick={() => handleEditCategory(sub)}
                            title="Editar"
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            className="btn-icon btn-danger"
                            onClick={() => handleDeleteCategory(sub.id)}
                            title="Eliminar"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </React.Fragment>
                );
              })
            }
            {/* Categorías sin padre que no son raíz (edge case) */}
            {categories.filter(c => c.parent_id && !categories.find(p => p.id === c.parent_id)).map(orphan => (
              <div key={orphan.id} className="settings-item">
                <div className="item-info">
                  <h3>{orphan.name}</h3>
                  <div className="category-badges">
                    <span className={`badge ${orphan.type === 'income' ? 'badge-success' : 'badge-danger'}`}>
                      {orphan.type === 'income' ? 'Ingreso' : 'Gasto'}
                    </span>
                    {orphan.is_personal && <span className="badge badge-warning">Personal</span>}
                    {orphan.allows_credit && <span className="badge badge-info">Crédito OK</span>}
                  </div>
                </div>
                <div className="item-actions">
                  <button className="btn-icon" onClick={() => handleEditCategory(orphan)} title="Editar">
                    <Edit2 size={16} />
                  </button>
                  <button className="btn-icon btn-danger" onClick={() => handleDeleteCategory(orphan.id)} title="Eliminar">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'creditCards' && (
        <div className="settings-section">
          <div className="section-header">
            <h2>Tarjetas de crédito</h2>
            <button className="btn-primary" onClick={handleAddCreditCard}>
              <Plus size={16} />
              Agregar tarjeta de crédito
            </button>
          </div>

          {showCreditCardForm && (
            <div className="form-card">
              <h3>{editingCreditCard ? 'Editar tarjeta de crédito' : 'Nueva tarjeta de crédito'}</h3>
              <div className="form-group">
                <label>Nombre de la tarjeta *</label>
                <input
                  type="text"
                  value={creditCardForm.name}
                  onChange={(e) => setCreditCardForm({ ...creditCardForm, name: e.target.value })}
                  placeholder="Ingresa el nombre de la tarjeta (p. ej., Visa Platinum)"
                />
              </div>
              <div className="form-group">
                <label>Titular (participante) *</label>
                <select
                  value={creditCardForm.participant_id}
                  onChange={(e) => setCreditCardForm({ ...creditCardForm, participant_id: e.target.value })}
                >
                  <option value="">Seleccionar participante</option>
                  {participants.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Día de cierre *</label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={creditCardForm.closing_day}
                    onChange={(e) => setCreditCardForm({
                      ...creditCardForm,
                      closing_day: parseInt(e.target.value)
                    })}
                  />
                  <small>Día del mes (1-31)</small>
                </div>
                <div className="form-group">
                  <label>Día de pago *</label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={creditCardForm.payment_day}
                    onChange={(e) => setCreditCardForm({
                      ...creditCardForm,
                      payment_day: parseInt(e.target.value)
                    })}
                  />
                  <small>Día del mes (1-31)</small>
                </div>
              </div>
              <div className="form-group">
                <label>Moneda *</label>
                <select
                  value={creditCardForm.currency}
                  onChange={(e) => setCreditCardForm({ ...creditCardForm, currency: e.target.value })}
                >
                  <option value="PEN">S/ Soles (PEN)</option>
                  <option value="USD">$ Dólares (USD)</option>
                </select>
              </div>
              <div className="form-actions">
                <button className="btn-primary" onClick={handleSaveCreditCard}>
                  <Save size={16} />
                  Guardar
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setShowCreditCardForm(false);
                    setEditingCreditCard(null);
                  }}
                >
                  <X size={16} />
                  Cancelar
                </button>
              </div>
            </div>
          )}

          <div className="settings-list">
            {creditCards.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                Aún no hay tarjetas de crédito. Agrega una para empezar a registrar gastos con crédito.
              </div>
            ) : (
              creditCards.map((card) => (
                <div key={card.id} className="settings-item">
                  <div className="item-info">
                    <h3>{card.name}</h3>
                    <p>
                      Titular: {participants.find(p => p.id === card.participant_id)?.name || 'Desconocido'} •
                      Cierre: día {card.closing_day} •
                      Pago: día {card.payment_day} •
                      {card.currency === 'USD' ? '$ USD' : 'S/ PEN'}
                    </p>
                  </div>
                  <div className="item-actions">
                    <button
                      className="btn-icon"
                      onClick={() => handleEditCreditCard(card)}
                      title="Editar"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      className="btn-icon btn-danger"
                      onClick={() => handleDeleteCreditCard(card.id)}
                      title="Eliminar"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

