import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Users, Tag, DollarSign, Plus, Edit2, Trash2, Save, X } from 'lucide-react';
import './Settings.css';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('participants');
  const [participants, setParticipants] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form states
  const [editingParticipant, setEditingParticipant] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [exchangeRates, setExchangeRates] = useState([]);
  const [showParticipantForm, setShowParticipantForm] = useState(false);
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [showExchangeRateForm, setShowExchangeRateForm] = useState(false);
  const [editingExchangeRate, setEditingExchangeRate] = useState(null);
  const [exchangeRateForm, setExchangeRateForm] = useState({ month: '', rate: '' });

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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [participantsData, categoriesData, ratesData] = await Promise.all([
        api.getParticipants(),
        api.getCategories(),
        api.getExchangeRates(),
      ]);
      setParticipants(participantsData);
      setCategories(categoriesData);
      setExchangeRates(ratesData);
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

  // Exchange Rate handlers
  const getCurrentMonthStr = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  };

  const handleAddExchangeRate = () => {
    setExchangeRateForm({ month: getCurrentMonthStr(), rate: '' });
    setEditingExchangeRate(null);
    setShowExchangeRateForm(true);
  };

  const handleEditExchangeRate = (rate) => {
    setExchangeRateForm({ month: rate.month, rate: rate.rate });
    setEditingExchangeRate(rate);
    setShowExchangeRateForm(true);
  };

  const handleSaveExchangeRate = async () => {
    try {
      const payload = {
        month: exchangeRateForm.month,
        from_currency: 'USD',
        to_currency: 'PEN',
        rate: parseFloat(exchangeRateForm.rate),
      };
      await api.upsertExchangeRate(payload);
      await loadData();
      setShowExchangeRateForm(false);
      setEditingExchangeRate(null);
    } catch (err) {
      alert('Error al guardar el tipo de cambio: ' + err.message);
    }
  };

  const handleDeleteExchangeRate = async (id) => {
    if (window.confirm('¿Eliminar este tipo de cambio?')) {
      try {
        await api.deleteExchangeRate(id);
        await loadData();
      } catch (err) {
        alert('Error al eliminar el tipo de cambio: ' + err.message);
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
          className={`tab-button ${activeTab === 'exchangeRates' ? 'active' : ''}`}
          onClick={() => setActiveTab('exchangeRates')}
        >
          <DollarSign size={20} />
          Tipos de cambio
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

      {activeTab === 'exchangeRates' && (
        <div className="settings-section">
          <div className="section-header">
            <h2>Tipos de cambio USD → PEN</h2>
            <button className="btn-primary" onClick={handleAddExchangeRate}>
              <Plus size={16} />
              Agregar tipo de cambio
            </button>
          </div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
            Configure el tipo de cambio por mes. Se usa para convertir transacciones en USD a PEN
            en reembolsos, presupuestos y estados contables.
          </p>

          {showExchangeRateForm && (
            <div className="form-card">
              <h3>{editingExchangeRate ? 'Editar tipo de cambio' : 'Nuevo tipo de cambio'}</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Mes *</label>
                  <input
                    type="month"
                    value={exchangeRateForm.month}
                    onChange={(e) => setExchangeRateForm({ ...exchangeRateForm, month: e.target.value })}
                    disabled={!!editingExchangeRate}
                  />
                </div>
                <div className="form-group">
                  <label>1 USD = ? PEN *</label>
                  <input
                    type="number"
                    min="0.000001"
                    step="0.01"
                    value={exchangeRateForm.rate}
                    onChange={(e) => setExchangeRateForm({ ...exchangeRateForm, rate: e.target.value })}
                    placeholder="Ej: 3.75"
                  />
                </div>
              </div>
              <div className="form-actions">
                <button className="btn-primary" onClick={handleSaveExchangeRate}>
                  <Save size={16} />
                  Guardar
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => { setShowExchangeRateForm(false); setEditingExchangeRate(null); }}
                >
                  <X size={16} />
                  Cancelar
                </button>
              </div>
            </div>
          )}

          <div className="settings-list">
            {exchangeRates.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                No hay tipos de cambio configurados. Agrega uno para cada mes con transacciones en USD.
              </div>
            ) : (
              [...exchangeRates]
                .sort((a, b) => b.month.localeCompare(a.month))
                .map((rate) => (
                  <div key={rate.id} className="settings-item">
                    <div className="item-info">
                      <h3>{rate.month}</h3>
                      <p>1 USD = <strong>S/ {parseFloat(rate.rate).toFixed(4)}</strong> PEN</p>
                    </div>
                    <div className="item-actions">
                      <button className="btn-icon" onClick={() => handleEditExchangeRate(rate)} title="Editar">
                        <Edit2 size={16} />
                      </button>
                      <button className="btn-icon btn-danger" onClick={() => handleDeleteExchangeRate(rate.id)} title="Eliminar">
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

