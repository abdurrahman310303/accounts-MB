import { useState, useEffect } from 'react'
import Modal from '../components/Modal'
import { accountAPI, formatCurrency } from '../services/api'

function Accounts() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    account_type: 'asset',
    default_currency: 'PKR',
    opening_balance: 0
  })

  const accountTypes = [
    { value: 'asset', label: 'Asset' },
    { value: 'liability', label: 'Liability' },
    { value: 'equity', label: 'Equity' },
    { value: 'income', label: 'Income' },
    { value: 'expense', label: 'Expense' },
    { value: 'business', label: 'Business' }
  ]

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await accountAPI.getAll()
      setAccounts(data)
    } catch (err) {
      setError('Failed to load accounts')
      console.error('Accounts error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openModal = (account = null) => {
    if (account) {
      setEditingAccount(account)
      setFormData({
        name: account.name,
        account_type: account.account_type,
        default_currency: account.default_currency,
        opening_balance: account.opening_balance
      })
    } else {
      setEditingAccount(null)
      setFormData({
        name: '',
        account_type: 'asset',
        default_currency: 'PKR',
        opening_balance: 0
      })
    }
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingAccount(null)
    setFormData({
      name: '',
      account_type: 'asset', 
      default_currency: 'PKR',
      opening_balance: 0
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingAccount) {
        await accountAPI.update(editingAccount.id, formData)
      } else {
        await accountAPI.create(formData)
      }
      closeModal()
      loadAccounts()
    } catch (err) {
      setError(`Failed to ${editingAccount ? 'update' : 'create'} account`)
      console.error('Account save error:', err)
    }
  }

  const handleDelete = async (account) => {
    if (window.confirm(`Are you sure you want to delete "${account.name}"?`)) {
      try {
        await accountAPI.delete(account.id)
        loadAccounts()
      } catch (err) {
        setError('Failed to delete account')
        console.error('Account delete error:', err)
      }
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading accounts...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Accounts</h1>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={() => openModal()}>
            Add Account
          </button>
        </div>
      </div>

      {error && (
        <div className="error">
          <p>{error}</p>
        </div>
      )}

      {accounts.length > 0 ? (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Currency</th>
                <th>Opening Balance</th>
                <th>Current Balance</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.id}>
                  <td>
                    <strong>{account.name}</strong>
                  </td>
                  <td style={{textTransform: 'capitalize'}}>{account.account_type}</td>
                  <td>{account.default_currency}</td>
                  <td className={account.opening_balance >= 0 ? 'positive' : 'negative'}>
                    {formatCurrency(account.opening_balance, account.default_currency)}
                  </td>
                  <td className={account.current_balance >= 0 ? 'positive' : 'negative'}>
                    {formatCurrency(account.current_balance, account.default_currency)}
                  </td>
                  <td>
                    <button 
                      className="btn btn-small"
                      onClick={() => openModal(account)}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-small"
                      onClick={() => handleDelete(account)}
                      style={{marginLeft: '0.5rem'}}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card text-center">
          <p>No accounts found.</p>
          <button className="btn btn-primary" onClick={() => openModal()}>
            Create your first account
          </button>
        </div>
      )}

      <Modal 
        isOpen={showModal} 
        onClose={closeModal}
        title={editingAccount ? 'Edit Account' : 'Add Account'}
      >
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Name</label>
            <input
              type="text"
              className="form-input"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Account Type</label>
            <select
              className="form-input"
              value={formData.account_type}
              onChange={(e) => setFormData({...formData, account_type: e.target.value})}
              required
            >
              {accountTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Currency</label>
            <select
              className="form-input"
              value={formData.default_currency}
              onChange={(e) => setFormData({...formData, default_currency: e.target.value})}
            >
              <option value="PKR">PKR - Pakistani Rupee</option>
              <option value="USD">USD - US Dollar</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Opening Balance</label>
            <input
              type="number"
              step="0.01"
              className="form-input"
              value={formData.opening_balance}
              onChange={(e) => setFormData({...formData, opening_balance: parseFloat(e.target.value) || 0})}
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn" onClick={closeModal}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {editingAccount ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default Accounts
