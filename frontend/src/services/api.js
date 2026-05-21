// API client for backend communication
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

        // Handle validation errors (422) with detailed messages
        let errorMessage = error.detail || `HTTP error ${response.status}`;
        if (Array.isArray(error.detail)) {
          // Pydantic validation errors
          errorMessage = error.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
        } else if (typeof error.detail === 'object') {
          errorMessage = JSON.stringify(error.detail);
        }

        // Create error object with status code
        const apiError = new Error(errorMessage);
        apiError.status = response.status;

        throw apiError;
      }

      // Handle 204 No Content (e.g., from DELETE operations)
      if (response.status === 204) {
        return null;
      }

      return await response.json();
    } catch (error) {
      // Handle 404 as a warning (expected for "no data yet" scenarios)
      if (error.status === 404) {
        console.warn(`API Warning [${endpoint}]:`, error.message);
      } else if (error.message && !error.message.includes('HTTP error')) {
        // Network errors or other issues
        console.error(`API Error [${endpoint}]:`, error);
      } else {
        // Other HTTP errors (500, 401, etc.)
        console.error(`API Error [${endpoint}]:`, error);
      }
      throw error;
    }
  }

  // GET request
  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  // POST request
  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // PUT request
  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // DELETE request
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // File upload
  async uploadFile(endpoint, file) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request(endpoint, {
      method: 'POST',
      headers: {}, // Let browser set Content-Type with boundary
      body: formData,
    });
  }
}

// API endpoints organized by resource
const api = new ApiClient();

export const participantsApi = {
  getAll: () => api.get('/participants'),
  getById: (id) => api.get(`/participants/${id}`),
  create: (data) => api.post('/participants', data),
  update: (id, data) => api.put(`/participants/${id}`, data),
  delete: (id) => api.delete(`/participants/${id}`),
};

export const categoriesApi = {
  getAll: () => api.get('/categories'),
  getById: (id) => api.get(`/categories/${id}`),
  create: (data) => api.post('/categories', data),
  update: (id, data) => api.put(`/categories/${id}`, data),
  delete: (id) => api.delete(`/categories/${id}`),
};

export const budgetApi = {
  getAll: () => api.get('/budget'),
  getByMonth: (month) => api.get(`/budget/month/${month}`),
  getVsActual: (month) => api.get(`/budget/vs-actual/${month}`),
  create: (data) => api.post('/budget', data),
  update: (id, data) => api.put(`/budget/${id}`, data),
  delete: (id) => api.delete(`/budget/${id}`),
  copyFromMonth: (fromMonth, toMonth) => api.post(`/budget/copy/${fromMonth}/${toMonth}`),
};

export const transactionsApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return api.get(`/transactions${query ? `?${query}` : ''}`);
  },
  getById: (id) => api.get(`/transactions/${id}`),
  create: (data) => api.post('/transactions', data),
  update: (id, data) => api.put(`/transactions/${id}`, data),
  delete: (id) => api.delete(`/transactions/${id}`),
  getByMonth: (month) => api.get(`/transactions/month/${month}`),
};

export const creditCardsApi = {
  getAll: () => api.get('/credit-cards'),
  getById: (id) => api.get(`/credit-cards/${id}`),
  create: (data) => api.post('/credit-cards', data),
  update: (id, data) => api.put(`/credit-cards/${id}`, data),
  delete: (id) => api.delete(`/credit-cards/${id}`),
  getInstallments: (cardId) => api.get(`/credit-cards/${cardId}/installments`),
};

export const debitCardsApi = {
  getAll: () => api.get('/debit-cards'),
  getById: (id) => api.get(`/debit-cards/${id}`),
  create: (data) => api.post('/debit-cards', data),
  update: (id, data) => api.put(`/debit-cards/${id}`, data),
  delete: (id) => api.delete(`/debit-cards/${id}`),
  getBalance: (id) => api.get(`/debit-cards/${id}/balance`),
};

export const installmentsApi = {
  getAll: () => api.get('/installments'),
  getByMonth: (month) => api.get(`/installments/month/${month}`),
  markPaid: (id, paid = true) => api.request(`/installments/${id}/mark-paid?paid=${paid}`, { method: 'PATCH' }),
  update: (id, data) => api.put(`/installments/${id}`, data),
};

export const reimbursementsApi = {
  getAll: () => api.get('/reimbursements'),
  getByMonth: (month) => api.get(`/reimbursements/month/${month}`),
  calculate: (month) => api.post(`/reimbursements/calculate/${month}`),
  finalize: (month) => api.post(`/reimbursements/finalize/${month}`),
  getBalanceSummary: (month) => api.get(`/reimbursements/balance/${month}`),
  markPaid: (id) => api.put(`/reimbursements/${id}/paid`),
};

export const simulationApi = {
  getAll: () => api.get('/expected-purchases'),
  create: (data) => api.post('/expected-purchases', data),
  update: (id, data) => api.put(`/expected-purchases/${id}`, data),
  delete: (id) => api.delete(`/expected-purchases/${id}`),
  simulate: () => api.get('/expected-purchases/simulate'),
};

export const statementsApi = {
  getIncomeStatement: (startDate, endDate) =>
    api.get(`/statements/income?start_date=${startDate}&end_date=${endDate}`),
  getCashFlow: (startDate, endDate) =>
    api.get(`/statements/cash-flow?start_date=${startDate}&end_date=${endDate}`),
  getBalanceSheet: (date) =>
    api.get(`/statements/balance-sheet?date=${date}`),
};

export const cashFlowApi = {
  getMonthly: (month) => api.get(`/cash-flow/month/${month}`),
  getSummary: (month) => api.get(`/cash-flow/summary/${month}`),
};

export const csvApi = {
  import: (file) => api.uploadFile('/csv/import', file),
  validate: (file) => api.uploadFile('/csv/validate', file),
};

// Unified API interface for easier imports
export const unifiedApi = {
  // Participants
  getParticipants: () => participantsApi.getAll(),
  getParticipant: (id) => participantsApi.getById(id),
  createParticipant: (data) => participantsApi.create(data),
  updateParticipant: (id, data) => participantsApi.update(id, data),
  deleteParticipant: (id) => participantsApi.delete(id),

  // Categories
  getCategories: () => categoriesApi.getAll(),
  getCategory: (id) => categoriesApi.getById(id),
  createCategory: (data) => categoriesApi.create(data),
  updateCategory: (id, data) => categoriesApi.update(id, data),
  deleteCategory: (id) => categoriesApi.delete(id),

  // Budget
  getBudget: () => budgetApi.getAll(),
  getBudgetByMonth: (month) => budgetApi.getByMonth(month),
  createBudget: (data) => budgetApi.create(data),
  updateBudget: (id, data) => budgetApi.update(id, data),
  deleteBudget: (id) => budgetApi.delete(id),

  // Transactions
  getTransactions: (params) => transactionsApi.getAll(params),
  getTransaction: (id) => transactionsApi.getById(id),
  createTransaction: (data) => transactionsApi.create(data),
  updateTransaction: (id, data) => transactionsApi.update(id, data),
  deleteTransaction: (id) => transactionsApi.delete(id),
  getTransactionsByMonth: (month) => transactionsApi.getByMonth(month),

  // Credit Cards
  getCreditCards: () => creditCardsApi.getAll(),
  getCreditCard: (id) => creditCardsApi.getById(id),
  createCreditCard: (data) => creditCardsApi.create(data),
  updateCreditCard: (id, data) => creditCardsApi.update(id, data),
  deleteCreditCard: (id) => creditCardsApi.delete(id),
  getCardInstallments: (cardId) => creditCardsApi.getInstallments(cardId),

  // Installments
  getInstallments: () => installmentsApi.getAll(),
  getInstallmentsByMonth: (month) => installmentsApi.getByMonth(month),

  // Reimbursements
  getReimbursements: () => reimbursementsApi.getAll(),
  getReimbursementsByMonth: (month) => reimbursementsApi.getByMonth(month),
  calculateReimbursements: (month) => reimbursementsApi.calculate(month),
  markReimbursementPaid: (id) => reimbursementsApi.markPaid(id),

  // Simulation
  getExpectedPurchases: () => simulationApi.getAll(),
  createExpectedPurchase: (data) => simulationApi.create(data),
  updateExpectedPurchase: (id, data) => simulationApi.update(id, data),
  deleteExpectedPurchase: (id) => simulationApi.delete(id),
  simulateExpectedPurchases: () => simulationApi.simulate(),

  // Statements
  getIncomeStatement: (startDate, endDate) => statementsApi.getIncomeStatement(startDate, endDate),
  getCashFlow: (startDate, endDate) => statementsApi.getCashFlow(startDate, endDate),
  getBalanceSheet: (date) => statementsApi.getBalanceSheet(date),

  // CSV
  importCSV: (file) => csvApi.import(file),
  validateCSV: (file) => csvApi.validate(file),
};

export { unifiedApi as api };
export default unifiedApi;
