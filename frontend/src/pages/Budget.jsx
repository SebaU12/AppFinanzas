import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, TrendingUp, TrendingDown, X, Save } from 'lucide-react';
import { budgetApi, categoriesApi } from '../services/api';
import { getCurrentMonth } from '../utils/formatters';

export default function Budget() {
  const [budgetData, setBudgetData] = useState(null);
  const [budgetEntries, setBudgetEntries] = useState([]); // Raw budget entries with IDs
  const [categories, setCategories] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth());
  const [tempMonth, setTempMonth] = useState(getCurrentMonth());
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [budgetForm, setBudgetForm] = useState({
    parent_category_id: '',
    category_id: '',
    budgeted_amount: 0
  });
  const [editingBudget, setEditingBudget] = useState(null);

  useEffect(() => {
    fetchBudgetData();
    fetchCategories();
  }, [selectedMonth]);

  const fetchBudgetData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [vsActualData, rawBudgets] = await Promise.all([
        budgetApi.getVsActual(selectedMonth),
        budgetApi.getByMonth(selectedMonth)
      ]);
      setBudgetData(vsActualData);
      setBudgetEntries(rawBudgets);
    } catch (err) {
      console.error('Error fetching budget data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const data = await categoriesApi.getAll();
      setCategories(data);
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  const handleAddBudget = () => {
    const firstParent = categories.find(c => !c.parent_id);
    setBudgetForm({
      parent_category_id: firstParent?.id || '',
      category_id: '',
      budgeted_amount: 0
    });
    setEditingBudget(null);
    setShowModal(true);
  };

  const handleEditBudget = (categoryId) => {
    // Find the budget entry for this category
    const budgetEntry = budgetEntries.find(b => b.category_id === categoryId);
    if (!budgetEntry) return;

    // Find the category to get parent info
    const category = categories.find(c => c.id === categoryId);
    const parentId = category?.parent_id || categoryId;

    setBudgetForm({
      parent_category_id: parentId,
      category_id: categoryId,
      budgeted_amount: budgetEntry.budgeted_amount
    });
    setEditingBudget(budgetEntry);
    setShowModal(true);
  };

  const handleSaveBudget = async () => {
    try {
      if (editingBudget) {
        // Update existing budget
        await budgetApi.update(editingBudget.id, {
          budgeted_amount: parseFloat(budgetForm.budgeted_amount)
        });
      } else {
        // Create new budget
        await budgetApi.create({
          month: selectedMonth,
          category_id: budgetForm.category_id,
          budgeted_amount: parseFloat(budgetForm.budgeted_amount)
        });
      }
      setShowModal(false);
      setEditingBudget(null);
      await fetchBudgetData();
    } catch (err) {
      alert('Error al guardar el presupuesto: ' + err.message);
    }
  };

  const getPreviousMonth = (month) => {
    const [year, monthNum] = month.split('-').map(Number);
    if (monthNum === 1) {
      return `${year - 1}-12`;
    }
    return `${year}-${String(monthNum - 1).padStart(2, '0')}`;
  };

  const handleCopyFromPreviousMonth = async () => {
    try {
      const previousMonth = getPreviousMonth(selectedMonth);
      const result = await budgetApi.copyFromMonth(previousMonth, selectedMonth);
      alert(`Se copiaron ${result.copied} presupuestos de ${previousMonth}. ${result.skipped} ya existían.`);
      await fetchBudgetData();
    } catch (err) {
      alert('Error al copiar presupuestos: ' + err.message);
    }
  };

  const renderCategoryRow = (category, isSubcategory = false) => {
    const isOverBudget = category.variance < 0;
    const isNearBudget = category.percentage >= 90 && category.percentage < 100;
    const hasBudget = category.budgeted > 0;

    let statusColor = '#569B85'; // Green - under budget
    if (isOverBudget) statusColor = '#E78484'; // Red - over budget
    else if (isNearBudget) statusColor = '#FFC145'; // Yellow - near budget

    return (
      <tr
        key={category.id}
        style={{
          borderBottom: '1px solid #e0e0e0',
          background: isSubcategory ? 'transparent' : '#f9f9f9'
        }}
      >
        <td style={{
          padding: '0.75rem 1rem',
          paddingLeft: isSubcategory ? '3rem' : '1rem',
          fontWeight: isSubcategory ? 400 : 600
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {category.name}
            {hasBudget && (
              <button
                onClick={() => handleEditBudget(category.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '0.25rem',
                  display: 'flex',
                  color: 'var(--primary)',
                  opacity: 0.6
                }}
                title="Editar presupuesto"
              >
                <Edit size={14} />
              </button>
            )}
          </div>
        </td>
        <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
          S/ {category.budgeted.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </td>
        <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
          S/ {category.actual.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </td>
        <td style={{
          padding: '0.75rem 1rem',
          textAlign: 'right',
          color: isOverBudget ? '#E78484' : '#569B85',
          fontWeight: 600
        }}>
          S/ {Math.abs(category.variance).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          {isOverBudget ? ' excedido' : ' por debajo'}
        </td>
        <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.5rem' }}>
            <div style={{
              width: '60px',
              height: '8px',
              background: '#e0e0e0',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${Math.min(category.percentage, 100)}%`,
                height: '100%',
                background: statusColor,
                transition: 'width 0.3s'
              }} />
            </div>
            <span style={{
              minWidth: '50px',
              color: statusColor,
              fontWeight: 600
            }}>
              {category.percentage}%
            </span>
          </div>
        </td>
      </tr>
    );
  };

  const renderCategorySection = (title, data, icon) => {
    if (!data || data.categories.length === 0) return null;

    return (
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          {icon}
          <h3 style={{ margin: 0 }}>{title}</h3>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--primary)' }}>
                <th style={{ textAlign: 'left', padding: '1rem' }}>Categoría</th>
                <th style={{ textAlign: 'right', padding: '1rem' }}>Presupuestado</th>
                <th style={{ textAlign: 'right', padding: '1rem' }}>Real</th>
                <th style={{ textAlign: 'right', padding: '1rem' }}>Diferencia</th>
                <th style={{ textAlign: 'right', padding: '1rem' }}>Progreso</th>
              </tr>
            </thead>
            <tbody>
              {data.categories.map(category => (
                <React.Fragment key={category.id}>
                  {renderCategoryRow(category, false)}
                  {category.subcategories?.map(subcat => renderCategoryRow(subcat, true))}
                </React.Fragment>
              ))}
              <tr style={{ borderTop: '2px solid var(--primary)', background: '#f0f0f0', fontWeight: 700 }}>
                <td style={{ padding: '1rem' }}>Total {title}</td>
                <td style={{ padding: '1rem', textAlign: 'right' }}>
                  S/ {data.total_budgeted.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td style={{ padding: '1rem', textAlign: 'right' }}>
                  S/ {data.total_actual.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td style={{
                  padding: '1rem',
                  textAlign: 'right',
                  color: data.variance < 0 ? '#E78484' : '#569B85'
                }}>
                  S/ {Math.abs(data.variance).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  {data.variance < 0 ? ' excedido' : ' por debajo'}
                </td>
                <td style={{ padding: '1rem' }}></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Cargando datos del presupuesto...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Presupuesto</h1>
          <p className="text-secondary">Seguimiento mensual: presupuesto vs real</p>
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
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn" onClick={handleCopyFromPreviousMonth} title="Copiar presupuestos del mes anterior">
            Copiar anterior
          </button>
          <button className="btn btn-primary" onClick={handleAddBudget}>
            <Plus size={20} />
            Nuevo presupuesto
          </button>
        </div>
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

      {budgetData && (
        <>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="card" style={{ background: 'linear-gradient(135deg, var(--primary), var(--primary-dark))', color: 'white' }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Ingresos presupuestados</p>
              <h2 style={{ margin: 0 }}>S/ {budgetData.income.total_budgeted.toLocaleString()}</h2>
            </div>
            <div className="card" style={{ background: 'linear-gradient(135deg, #569B85, #3d7a61)', color: 'white' }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Ingresos reales</p>
              <h2 style={{ margin: 0 }}>S/ {budgetData.income.total_actual.toLocaleString()}</h2>
            </div>
            <div className="card" style={{ background: 'linear-gradient(135deg, var(--accent), #c66666)', color: 'white' }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Gastos presupuestados</p>
              <h2 style={{ margin: 0 }}>S/ {budgetData.expenses.total_budgeted.toLocaleString()}</h2>
            </div>
            <div className="card" style={{ background: 'linear-gradient(135deg, #E78484, #c66666)', color: 'white' }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Gastos reales</p>
              <h2 style={{ margin: 0 }}>S/ {budgetData.expenses.total_actual.toLocaleString()}</h2>
            </div>
            <div className="card" style={{
              background: budgetData.net.actual >= 0
                ? 'linear-gradient(135deg, var(--secondary), #e6a830)'
                : 'linear-gradient(135deg, #8a5a44, #5c3a2e)',
              color: 'white'
            }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Neto (presupuestado)</p>
              <h2 style={{ margin: 0 }}>S/ {budgetData.net.budgeted.toLocaleString()}</h2>
            </div>
            <div className="card" style={{
              background: budgetData.net.actual >= 0
                ? 'linear-gradient(135deg, #569B85, #3d7a61)'
                : 'linear-gradient(135deg, var(--accent), #c66666)',
              color: 'white'
            }}>
              <p style={{ opacity: 0.9, marginBottom: '0.5rem' }}>Neto (real)</p>
              <h2 style={{ margin: 0 }}>S/ {budgetData.net.actual.toLocaleString()}</h2>
            </div>
          </div>

          {/* Income Budget Table */}
          {renderCategorySection(
            'Ingresos',
            budgetData.income,
            <TrendingUp size={24} style={{ color: 'var(--primary)' }} />
          )}

          {/* Expense Budget Table */}
          {renderCategorySection(
            'Gastos',
            budgetData.expenses,
            <TrendingDown size={24} style={{ color: 'var(--accent)' }} />
          )}

          {/* No data message */}
          {budgetData.income.total_budgeted === 0 && budgetData.expenses.total_budgeted === 0 && (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <h3 style={{ marginBottom: '0.5rem' }}>No hay presupuesto configurado para {selectedMonth}</h3>
              <p className="text-secondary" style={{ marginBottom: '1.5rem' }}>
                Aún no has configurado presupuestos para este mes
              </p>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={handleCopyFromPreviousMonth}>
                  <Plus size={20} />
                  Copiar del mes anterior
                </button>
                <button className="btn" onClick={handleAddBudget}>
                  <Plus size={20} />
                  Agregar presupuesto manualmente
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Add/Edit Budget Modal */}
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
              <h2 style={{ margin: 0 }}>{editingBudget ? 'Editar presupuesto' : 'Nuevo presupuesto'}</h2>
              <button
                onClick={() => {
                  setShowModal(false);
                  setEditingBudget(null);
                }}
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
              {!editingBudget && (
                <>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                      Categoría padre *
                    </label>
                    <select
                      value={budgetForm.parent_category_id}
                      onChange={(e) => setBudgetForm({
                        ...budgetForm,
                        parent_category_id: e.target.value,
                        category_id: '' // Reset subcategory when parent changes
                      })}
                      className="input"
                    >
                      <option value="">Seleccionar categoría padre</option>
                      {categories
                        .filter(c => !c.parent_id)
                        .map(parent => (
                          <option key={parent.id} value={parent.id}>
                            {parent.name}
                          </option>
                        ))}
                    </select>
                  </div>

                  {budgetForm.parent_category_id && (
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                        Subcategoría *
                      </label>
                      <select
                        value={budgetForm.category_id}
                        onChange={(e) => setBudgetForm({ ...budgetForm, category_id: e.target.value })}
                        className="input"
                      >
                        <option value="">Seleccionar subcategoría</option>
                        <option value={budgetForm.parent_category_id}>
                          {categories.find(c => c.id === budgetForm.parent_category_id)?.name} (Total)
                        </option>
                        {categories
                          .filter(c => c.parent_id === budgetForm.parent_category_id)
                          .map(child => (
                            <option key={child.id} value={child.id}>
                              {child.name}
                            </option>
                          ))}
                      </select>
                    </div>
                  )}
                </>
              )}

              {editingBudget && (
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Categoría
                  </label>
                  <div style={{
                    padding: '0.75rem',
                    background: '#f5f5f5',
                    borderRadius: '0.5rem',
                    fontWeight: 600
                  }}>
                    {categories.find(c => c.id === budgetForm.category_id)?.name}
                  </div>
                </div>
              )}

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Monto presupuestado *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={budgetForm.budgeted_amount}
                  onChange={(e) => setBudgetForm({ ...budgetForm, budgeted_amount: e.target.value })}
                  className="input"
                  placeholder="0.00"
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleSaveBudget}
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

