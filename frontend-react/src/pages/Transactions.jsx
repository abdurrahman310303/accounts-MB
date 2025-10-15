import { useState, useEffect } from 'react'
import Modal from '../components/Modal'
import { transactionAPI, accountAPI, categoryAPI, teamAPI, formatCurrency, formatCurrencyCompact, formatDate } from '../services/api'

function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [allTransactions, setAllTransactions] = useState([]) // Store all transactions for filtering
  const [accounts, setAccounts] = useState([])
  const [categories, setCategories] = useState([])
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState(null)
  
  // Filter states
  const [filters, setFilters] = useState({
    accountId: '',
    categoryId: '',
    startDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0], // First day of current month
    endDate: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().split('T')[0] // Last day of current month
  })
  
  const [formData, setFormData] = useState({
    account_id: '',
    amount: '',
    description: '',
    transaction_date: new Date().toISOString().split('T')[0],
    category_id: '',
    team_id: '',
    counterparty: '',
    currency: 'PKR'
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [transactionsData, accountsData, categoriesData, teamsData] = await Promise.all([
        transactionAPI.getAll({ limit: 50 }),
        accountAPI.getAll(),
        categoryAPI.getAll(),
        teamAPI.getAll()
      ])
      
      setAllTransactions(transactionsData)
      setTransactions(transactionsData)
      setAccounts(accountsData)
      setCategories(categoriesData)
      setTeams(teamsData)
      
      // Apply initial filter after loading data
      setTimeout(() => applyFilters(transactionsData), 0)
    } catch (err) {
      setError('Failed to load transactions')
      console.error('Transactions error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openModal = (transaction = null) => {
    if (transaction) {
      setEditingTransaction(transaction)
      setFormData({
        account_id: transaction.account_id,
        amount: Math.abs(transaction.amount),
        description: transaction.description || '',
        transaction_date: transaction.transaction_date,
        category_id: transaction.category_id || '',
        team_id: transaction.team_id || '',
        counterparty: transaction.counterparty || '',
        currency: 'PKR'
      })
    } else {
      setEditingTransaction(null)
      setFormData({
        account_id: '',
        amount: 0,
        description: '',
        transaction_date: new Date().toISOString().split('T')[0],
        category_id: '',
        team_id: '',
        counterparty: '',
        currency: 'PKR'
      })
    }
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingTransaction(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const transactionData = {
        ...formData,
        amount: parseFloat(formData.amount),
        account_id: parseInt(formData.account_id),
        category_id: formData.category_id ? parseInt(formData.category_id) : null,
        team_id: formData.team_id ? parseInt(formData.team_id) : null
      }

      if (editingTransaction) {
        await transactionAPI.update(editingTransaction.id, transactionData)
      } else {
        await transactionAPI.create(transactionData)
      }
      closeModal()
      await loadData()
    } catch (err) {
      // Handle specific error messages from the backend
      const errorMessage = err?.detail || err?.message || `Failed to ${editingTransaction ? 'update' : 'create'} transaction`
      setError(errorMessage)
      console.error('Transaction save error:', err)
    }
  }

  const handleDelete = async (transaction) => {
    if (window.confirm(`Are you sure you want to delete this transaction?`)) {
      try {
        await transactionAPI.delete(transaction.id)
        await loadData()
      } catch (err) {
        setError('Failed to delete transaction')
        console.error('Transaction delete error:', err)
      }
    }
  }

  const getAccountName = (accountId) => {
    const account = accounts.find(a => a.id === accountId)
    return account ? account.name : 'Unknown'
  }

  const getCategoryName = (categoryId) => {
    if (!categoryId) return '-'
    const category = categories.find(c => c.id === categoryId)
    return category ? category.name : 'Unknown'
  }

  const getTeamName = (teamId) => {
    if (!teamId) return '-'
    const team = teams.find(t => t.id === teamId)
    return team ? team.name : 'Unknown'
  }

  const getCounterpartyDisplay = (counterparty) => {
    if (!counterparty) return '-'
    if (counterparty === 'External') return 'External Party'
    // Check if counterparty matches an account name
    const account = accounts.find(a => a.name === counterparty)
    return account ? `${counterparty} (${account.account_type})` : counterparty
  }

  const applyFilters = (transactionsToFilter = allTransactions) => {
    let filtered = transactionsToFilter

    // Filter by account
    if (filters.accountId) {
      filtered = filtered.filter(t => t.account_id === parseInt(filters.accountId))
    }

    // Filter by category
    if (filters.categoryId) {
      filtered = filtered.filter(t => t.category_id === parseInt(filters.categoryId))
    }

    // Filter by date range
    if (filters.startDate) {
      filtered = filtered.filter(t => t.transaction_date >= filters.startDate)
    }
    if (filters.endDate) {
      filtered = filtered.filter(t => t.transaction_date <= filters.endDate)
    }

    setTransactions(filtered)
  }

  const handleFilterChange = (filterKey, value) => {
    const newFilters = { ...filters, [filterKey]: value }
    setFilters(newFilters)
    
    // Apply filters with updated values
    setTimeout(() => {
      let filtered = allTransactions

      // Filter by account
      if (newFilters.accountId) {
        filtered = filtered.filter(t => t.account_id === parseInt(newFilters.accountId))
      }

      // Filter by category
      if (newFilters.categoryId) {
        filtered = filtered.filter(t => t.category_id === parseInt(newFilters.categoryId))
      }

      // Filter by date range
      if (newFilters.startDate) {
        filtered = filtered.filter(t => t.transaction_date >= newFilters.startDate)
      }
      if (newFilters.endDate) {
        filtered = filtered.filter(t => t.transaction_date <= newFilters.endDate)
      }

      setTransactions(filtered)
    }, 0)
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading transactions...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Transactions</h1>
          <p style={{ margin: '0.5rem 0 0 0', color: '#666', fontSize: '0.9rem' }}>
            {transactions.length} transaction{transactions.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => openModal()}>
          Add Transaction
        </button>
      </div>

      {error && (
        <div className="error">
          <p>{error}</p>
        </div>
      )}

      {/* Quick Filters */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        marginBottom: '1rem',
        padding: '1rem',
        backgroundColor: 'white',
        border: '2px solid #000000',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <span style={{ fontWeight: '600', marginRight: '1rem' }}>Quick Filters:</span>
        <select 
          style={{
            padding: '0.5rem',
            border: '2px solid #000000',
            fontSize: '0.9rem',
            backgroundColor: 'white'
          }} 
          value={filters.accountId}
          onChange={(e) => handleFilterChange('accountId', e.target.value)}
        >
          <option value="">All Accounts</option>
          {accounts.map(account => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </select>
        <select 
          style={{
            padding: '0.5rem',
            border: '2px solid #000000',
            fontSize: '0.9rem',
            backgroundColor: 'white'
          }}
          value={filters.categoryId}
          onChange={(e) => handleFilterChange('categoryId', e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map(category => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        <input 
          type="date" 
          style={{
            padding: '0.5rem',
            border: '2px solid #000000',
            fontSize: '0.9rem',
            backgroundColor: 'white'
          }}
          value={filters.startDate}
          onChange={(e) => handleFilterChange('startDate', e.target.value)}
        />
        <span style={{ fontSize: '0.9rem', color: '#000000' }}>to</span>
        <input 
          type="date" 
          style={{
            padding: '0.5rem',
            border: '2px solid #000000',
            fontSize: '0.9rem',
            backgroundColor: 'white'
          }}
          value={filters.endDate}
          onChange={(e) => handleFilterChange('endDate', e.target.value)}
        />
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            style={{
              padding: '0.4rem 0.8rem',
              border: '2px solid #000000',
              fontSize: '0.85rem',
              backgroundColor: '#000000',
              color: 'white',
              cursor: 'pointer'
            }}
            onClick={() => {
              const today = new Date()
              const firstDay = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
              const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0]
              handleFilterChange('startDate', firstDay)
              handleFilterChange('endDate', lastDay)
            }}
          >
            This Month
          </button>
          <button 
            style={{
              padding: '0.4rem 0.8rem',
              border: '2px solid #000000',
              fontSize: '0.85rem',
              backgroundColor: 'white',
              color: '#000000',
              cursor: 'pointer'
            }}
            onClick={() => {
              const defaultFilters = {
                accountId: '',
                categoryId: '',
                startDate: '',
                endDate: ''
              }
              setFilters(defaultFilters)
              setTransactions(allTransactions)
            }}
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Filter Status */}
      <div style={{
        fontSize: '0.9rem',
        color: '#000000',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <span>Showing {transactions.length} of {allTransactions.length} transactions</span>
        {(filters.accountId || filters.categoryId || filters.startDate || filters.endDate) && (
          <span style={{ 
            padding: '0.2rem 0.5rem', 
            backgroundColor: 'white', 
            border: '1px solid #000000',
            fontSize: '0.8rem'
          }}>
            Filters active
          </span>
        )}
      </div>

      {transactions.length > 0 ? (
        <>
        {/* Summary Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          <div style={{
            padding: '1rem',
            backgroundColor: 'white',
            border: '2px solid #000000',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#38a169' }}>
              {(() => {
                const incomeTransactions = transactions.filter(t => {
                  const category = categories.find(c => c.id === t.category_id)
                  return category && category.category_type === 'income'
                })
                return incomeTransactions.length
              })()}
            </div>
            <div style={{ fontSize: '0.9rem', color: '#000000', marginTop: '0.25rem' }}>Income Transactions</div>
            <div style={{ fontSize: '0.8rem', color: '#38a169', marginTop: '0.25rem' }}>
              {(() => {
                const incomeAmount = transactions.reduce((sum, t) => {
                  const category = categories.find(c => c.id === t.category_id)
                  if (category && category.category_type === 'income') {
                    return sum + Math.abs(parseFloat(t.amount_pkr || 0))
                  }
                  return sum
                }, 0)
                return formatCurrencyCompact(incomeAmount, 'PKR')
              })()}
            </div>
          </div>
          <div style={{
            padding: '1rem',
            backgroundColor: 'white',
            border: '2px solid #000000',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#e53e3e' }}>
              {(() => {
                const expenseTransactions = transactions.filter(t => {
                  const category = categories.find(c => c.id === t.category_id)
                  return category && category.category_type === 'expense'
                })
                return expenseTransactions.length
              })()}
            </div>
            <div style={{ fontSize: '0.9rem', color: '#000000', marginTop: '0.25rem' }}>Expense Transactions</div>
            <div style={{ fontSize: '0.8rem', color: '#e53e3e', marginTop: '0.25rem' }}>
              {(() => {
                const expenseAmount = transactions.reduce((sum, t) => {
                  const category = categories.find(c => c.id === t.category_id)
                  if (category && category.category_type === 'expense') {
                    return sum + Math.abs(parseFloat(t.amount_pkr || 0))
                  }
                  return sum
                }, 0)
                return formatCurrencyCompact(expenseAmount, 'PKR')
              })()}
            </div>
          </div>
          <div style={{
            padding: '1rem',
            backgroundColor: 'white',
            border: '2px solid #000000',
            textAlign: 'center'
          }}>
            {(() => {
              const totalIncome = transactions.reduce((sum, t) => {
                const category = categories.find(c => c.id === t.category_id)
                if (category && category.category_type === 'income') {
                  return sum + Math.abs(parseFloat(t.amount_pkr || 0))
                }
                return sum
              }, 0)
              
              const totalExpenses = transactions.reduce((sum, t) => {
                const category = categories.find(c => c.id === t.category_id)
                if (category && category.category_type === 'expense') {
                  return sum + Math.abs(parseFloat(t.amount_pkr || 0))
                }
                return sum
              }, 0)
              
              const netAmount = totalIncome - totalExpenses
              
              return (
                <>
                  <div style={{ 
                    fontSize: '1.5rem', 
                    fontWeight: '700', 
                    color: netAmount >= 0 ? '#38a169' : '#e53e3e' 
                  }}>
                    {netAmount >= 0 ? '+' : ''}{formatCurrencyCompact(netAmount, 'PKR')}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#000000', marginTop: '0.25rem' }}>
                    Net Amount (Income - Expenses)
                  </div>
                  <div style={{ 
                    fontSize: '0.8rem', 
                    color: '#666666', 
                    marginTop: '0.25rem' 
                  }}>
                    {formatCurrency(netAmount, 'PKR')}
                  </div>
                </>
              )
            })()}
          </div>
        </div>

        {/* Opening Balance for Current Month */}
        {filters.startDate && (
          <div style={{
            backgroundColor: 'white',
            border: '2px solid #000000',
            marginBottom: '1rem'
          }}>
            <div style={{
              padding: '0.75rem 1rem',
              borderBottom: '1px solid #000000',
              backgroundColor: '#f8f8f8',
              fontSize: '1.1rem',
              fontWeight: '600',
              color: '#000000'
            }}>
              Opening Balance for {new Date(filters.startDate).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </div>
            {filters.accountId ? (() => {
              const account = accounts.find(a => a.id === parseInt(filters.accountId))
              if (!account) return null
              
              const startDate = new Date(filters.startDate)
              const transactionsBeforeStart = allTransactions.filter(t => 
                t.account_id === parseInt(filters.accountId) && 
                new Date(t.transaction_date) < startDate
              )
              const totalBeforeStart = transactionsBeforeStart.reduce((sum, t) => sum + parseFloat(t.amount_pkr || 0), 0)
              const accountOpeningBalance = parseFloat(account?.opening_balance || 0)
              const openingBalance = accountOpeningBalance + totalBeforeStart
              
              return (
                <div style={{
                  padding: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '2rem',
                  fontSize: '0.95rem'
                }}>
                  <div style={{ fontWeight: '600', minWidth: '150px' }}>
                    {account.name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontWeight: '600', color: '#000000' }}>
                        Rs.{parseFloat(openingBalance || 0).toFixed(2)}
                      </span>
                      <span style={{ fontSize: '0.85rem', color: '#666' }}>
                        (PKR)
                      </span>
                    </div>
                  </div>
                </div>
              )
            })() : (
              <div style={{
                padding: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '2rem',
                fontSize: '0.95rem'
              }}>
                <div style={{ fontWeight: '600', minWidth: '150px' }}>
                  All Accounts Combined
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: '600', color: '#000000' }}>
                      Rs.{(() => {
                        const startDate = new Date(filters.startDate)
                        const transactionsBeforeStart = allTransactions.filter(t => 
                          new Date(t.transaction_date) < startDate
                        )
                        const totalBeforeStart = transactionsBeforeStart.reduce((sum, t) => sum + parseFloat(t.amount_pkr || 0), 0)
                        const totalOpeningBalance = accounts.reduce((sum, acc) => sum + parseFloat(acc.opening_balance || 0), 0)
                        const openingBalance = totalOpeningBalance + totalBeforeStart
                        return openingBalance.toFixed(2)
                      })()}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: '#666' }}>
                      (PKR)
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ 
            overflow: 'auto', 
            maxWidth: '100%',
            border: '1px solid #000000'
          }}>
            <table className="table" style={{ 
              minWidth: '1400px', 
              fontSize: '0.9rem',
              tableLayout: 'auto',
              margin: '0',
              borderCollapse: 'collapse'
            }}>
            <thead>
              <tr>
                <th style={{ minWidth: '120px', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Account</th>
                <th style={{ minWidth: '100px', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Date</th>
                <th style={{ minWidth: '100px', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Category</th>
                <th style={{ minWidth: '80px', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Team</th>
                <th style={{ minWidth: '120px', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Counterparty</th>
                <th style={{ minWidth: '150px', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Description</th>
                <th style={{ minWidth: '130px', textAlign: 'right', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Amount (PKR)</th>
                <th style={{ minWidth: '130px', textAlign: 'right', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Currency</th>

                <th style={{ minWidth: '120px', textAlign: 'right', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Balance</th>
                <th style={{ minWidth: '100px', borderRight: '1px solid #484747ff', padding: '0.75rem 0.5rem' }}>Last Updated</th>
                <th style={{ minWidth: '120px', textAlign: 'center', padding: '0.75rem 0.5rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.id} style={{ borderBottom: '1px solid #000000' }}>
                  <td style={{ fontWeight: '600', padding: '0.75rem 0.5rem', borderRight: '1px solid #e0e0e0' }}>
                    {getAccountName(transaction.account_id)}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', borderRight: '1px solid #e0e0e0' }}>
                    {formatDate(transaction.transaction_date)}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', borderRight: '1px solid #e0e0e0' }}>
                    <span style={{ 
                      padding: '0.2rem 0.5rem',
                      backgroundColor: (() => {
                        const category = categories.find(c => c.id === transaction.category_id)
                        if (!category) return 'white'
                        return category.category_type === 'income' ? '#dcfce7' : 
                               category.category_type === 'expense' ? '#fef2f2' : '#dbeafe'
                      })(),
                      color: (() => {
                        const category = categories.find(c => c.id === transaction.category_id)
                        if (!category) return '#000000'
                        return category.category_type === 'income' ? '#166534' : 
                               category.category_type === 'expense' ? '#991b1b' : '#1e40af'
                      })(),
                      border: '1px solid #000000',
                      fontSize: '0.85rem',
                      fontWeight: '500'
                    }}>
                      {getCategoryName(transaction.category_id)}
                      {(() => {
                        const category = categories.find(c => c.id === transaction.category_id)
                        if (category) {
                          return category.category_type === 'income' ? ' ' : 
                                 category.category_type === 'expense' ? ' ' : ' '
                        }
                        return ''
                      })()}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', borderRight: '1px solid #e0e0e0' }}>
                    <span style={{ 
                      padding: '0.2rem 0.5rem',
                      backgroundColor: 'white',
                      border: '1px solid #000000',
                      fontSize: '0.85rem'
                    }}>
                      {getTeamName(transaction.team_id)}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', fontStyle: transaction.counterparty ? 'normal' : 'italic', color: transaction.counterparty ? 'inherit' : '#000000', borderRight: '1px solid #e0e0e0' }}>
                    <span style={{ 
                      padding: '0.2rem 0.5rem',
                      backgroundColor: 'white',
                      fontSize: '0.85rem',
                      border: transaction.counterparty ? '1px solid #000000' : 'none'
                    }}>
                      {getCounterpartyDisplay(transaction.counterparty)}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', borderRight: '1px solid #e0e0e0' }} title={transaction.description}>
                    {transaction.description || 'No description'}
                  </td>
                  <td style={{ 
                    padding: '0.75rem 0.5rem',
                    textAlign: 'right',
                    fontWeight: '600',
                    color: transaction.amount >= 0 ? '#38a169' : '#e53e3e',
                    borderRight: '1px solid #e0e0e0'
                  }}>
                    {transaction.amount >= 0 ? '+' : ''}{formatCurrency(transaction.amount, transaction.currency || 'PKR')}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'center', fontWeight: '600', borderRight: '1px solid #e0e0e0' }}>
                    {transaction.currency || 'PKR'}
                  </td>
                  <td style={{ 
                    padding: '0.75rem 0.5rem',
                    textAlign: 'right',
                    fontWeight: '600',
                    color: transaction.amount_pkr >= 0 ? '#38a169' : '#e53e3e',
                    fontFamily: 'monospace',
                    borderRight: '1px solid #e0e0e0'
                  }}>
                    {(() => {
                      const amountPkr = parseFloat(transaction.amount_pkr || 0)
                      return `${amountPkr >= 0 ? '+' : ''}Rs.${amountPkr.toFixed(2)}`
                    })()}
                  </td>
                  <td style={{ 
                    padding: '0.75rem 0.5rem',
                    textAlign: 'right',
                    fontWeight: '700',
                    backgroundColor: 'white',
                    fontFamily: 'monospace',
                    borderRight: '1px solid #e0e0e0'
                  }}>
                    {formatCurrency(transaction.balance_after, 'PKR')}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>
                    <button 
                      className="btn btn-small"
                      onClick={() => openModal(transaction)}
                      style={{ 
                        padding: '0.3rem 0.6rem',
                        fontSize: '0.8rem',
                        marginRight: '0.3rem',
                        border: '1px solid #000000',
                        backgroundColor: 'white',
                        color: '#000000'
                      }}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-small"
                      onClick={() => handleDelete(transaction)}
                      style={{ 
                        padding: '0.3rem 0.6rem',
                        fontSize: '0.8rem',
                        backgroundColor: '#000000',
                        color: 'white',
                        border: '1px solid #000000'
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
        </>
      ) : (
        <div className="card text-center">
          <p>No transactions found.</p>
          <button className="btn btn-primary" onClick={() => openModal()}>
            Create your first transaction
          </button>
        </div>
      )}

      <Modal 
        isOpen={showModal} 
        onClose={closeModal}
        title={editingTransaction ? 'Edit Transaction' : 'Add Transaction'}
      >
        <form onSubmit={handleSubmit}>
          <div style={{
            padding: '0.75rem',
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '4px',
            marginBottom: '1rem',
            fontSize: '0.85rem',
            color: '#4a5568'
          }}>
            <strong>💡 How it works:</strong>
            <ul style={{ margin: '0.5rem 0 0 1rem', paddingLeft: '0' }}>
              <li>• <strong>Income:</strong> Adds money to the selected account</li>
              <li>• <strong>Expense:</strong> Deducts money from the selected account</li>
              <li>• <strong>Transfer:</strong> Moves money between accounts (deducts from sender, adds to receiver)</li>
            </ul>
          </div>
          
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Account</label>
              <select
                className="form-input"
                value={formData.account_id}
                onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                required
              >
                <option value="">Select Account</option>
                {accounts.map(account => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                Amount
                {formData.category_id && (() => {
                  const category = categories.find(c => c.id === parseInt(formData.category_id))
                  if (category) {
                    return (
                      <span style={{ 
                        fontSize: '0.8rem', 
                        fontWeight: 'normal',
                        marginLeft: '0.5rem',
                        color: category.category_type === 'expense' ? '#dc2626' : 
                              category.category_type === 'income' ? '#16a34a' : '#2563eb'
                      }}>
                        {category.category_type === 'expense' && '(will be deducted from account)'}
                        {category.category_type === 'income' && '(will be added to account)'}
                        {category.category_type === 'transfer' && '(transfer amount)'}
                      </span>
                    )
                  }
                })()}
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="form-input"
                value={formData.amount}
                onChange={(e) => setFormData({...formData, amount: e.target.value})}
                placeholder="Enter positive amount"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <input
              type="text"
              className="form-input"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category (determines transaction behavior)</label>
            <select
              className="form-input"
              value={formData.category_id}
              onChange={(e) => setFormData({...formData, category_id: e.target.value})}
              required
            >
              <option value="">Select Category</option>
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.name} - {category.category_type === 'income' ? ' Income (adds to account)' : 
                                     category.category_type === 'expense' ? ' Expense (deducts from account)' : 
                                     ' Transfer (moves between accounts)'}
                </option>
              ))}
            </select>
          </div>

          {/* Show Counterparty field only when category is transfer */}
          {(() => {
            const selectedCategory = categories.find(cat => cat.id === parseInt(formData.category_id))
            return selectedCategory?.category_type === 'transfer' && (
              <div className="form-group">
                <label className="form-label">Counterparty Account</label>
                <select
                  className="form-input"
                  value={formData.counterparty}
                  onChange={(e) => setFormData({...formData, counterparty: e.target.value})}
                >
                  <option value="">Select Counterparty Account</option>
                  <option value="External">External (Non-account)</option>
                  <optgroup label="Internal Accounts">
                    {accounts.map(account => (
                      <option key={account.id} value={account.name}>
                        {account.name} ({account.account_type})
                      </option>
                    ))}
                  </optgroup>
                </select>
              </div>
            )
          })()}

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Date</label>
              <input
                type="date"
                className="form-input"
                value={formData.transaction_date}
                onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Currency</label>
              <select
                className="form-input"
                value={formData.currency || 'PKR'}
                onChange={(e) => setFormData({...formData, currency: e.target.value})}
                disabled
                style={{ backgroundColor: '#f5f5f5', color: '#666' }}
              >
                <option value="PKR">PKR (Pakistani Rupee)</option>
              </select>
            </div>
          </div>

          {/* Balance Impact Preview */}
          {formData.account_id && formData.amount !== '' && formData.amount !== 0 && formData.category_id && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: '#f0f9ff',
              border: '1px solid #bfdbfe',
              borderRadius: '4px',
              marginBottom: '1rem'
            }}>
              <div style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Balance Impact Preview:
              </div>
              <div style={{ fontSize: '0.85rem', color: '#666' }}>
                {(() => {
                  const account = accounts.find(a => a.id === parseInt(formData.account_id))
                  const category = categories.find(c => c.id === parseInt(formData.category_id))
                  if (!account || !category) return 'Select account and category to see balance impact'
                  
                  const currentBalance = parseFloat(account.current_balance || 0)
                  const enteredAmount = parseFloat(formData.amount)
                  
                  // Determine actual transaction impact based on category type
                  let actualAmount = 0
                  let isInterAccountTransfer = false
                  
                  if (category.category_type === 'expense') {
                    // Expenses are always negative (money going out)
                    actualAmount = -Math.abs(enteredAmount)
                  } else if (category.category_type === 'income') {
                    // Income is always positive (money coming in)
                    actualAmount = Math.abs(enteredAmount)
                  } else if (category.category_type === 'transfer') {
                    // For transfers, check if it's inter-account
                    isInterAccountTransfer = formData.counterparty && formData.counterparty !== 'External' && 
                      accounts.some(a => a.name === formData.counterparty)
                    
                    if (isInterAccountTransfer) {
                      // Inter-account transfer: sender gets negative, receiver gets positive
                      actualAmount = -Math.abs(enteredAmount)
                    } else {
                      // External transfer: could be positive (receiving) or negative (sending)
                      // For simplicity, let user decide the sign
                      actualAmount = enteredAmount
                    }
                  }
                  
                  const newBalance = currentBalance + actualAmount
                  
                  const result = (
                    <div>
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>{account.name}:</strong> Rs.{currentBalance.toFixed(2)} → Rs.{newBalance.toFixed(2)}
                        <span style={{ 
                          color: actualAmount >= 0 ? '#38a169' : '#e53e3e',
                          marginLeft: '0.5rem',
                          fontWeight: '600'
                        }}>
                          ({actualAmount >= 0 ? '+' : ''}Rs.{Math.abs(actualAmount).toFixed(2)})
                        </span>
                        <span style={{ 
                          marginLeft: '0.5rem',
                          fontSize: '0.8rem',
                          color: category.category_type === 'expense' ? '#dc2626' : 
                                category.category_type === 'income' ? '#16a34a' : '#2563eb',
                          fontWeight: '500'
                        }}>
                          ({category.category_type})
                        </span>
                      </div>
                      
                      {isInterAccountTransfer && formData.counterparty && (
                        <div style={{ 
                          marginTop: '0.5rem', 
                          paddingTop: '0.5rem', 
                          borderTop: '1px solid #e2e8f0' 
                        }}>
                          {(() => {
                            const counterpartyAccount = accounts.find(a => a.name === formData.counterparty)
                            if (!counterpartyAccount) return null
                            
                            const counterpartyBalance = parseFloat(counterpartyAccount.current_balance || 0)
                            const receiverAmount = Math.abs(enteredAmount)
                            const counterpartyNewBalance = counterpartyBalance + receiverAmount
                            
                            return (
                              <div>
                                <strong>{counterpartyAccount.name}:</strong> Rs.{counterpartyBalance.toFixed(2)} → Rs.{counterpartyNewBalance.toFixed(2)}
                                <span style={{ 
                                  color: '#38a169',
                                  marginLeft: '0.5rem',
                                  fontWeight: '600'
                                }}>
                                  (+Rs.{receiverAmount.toFixed(2)})
                                </span>
                                <span style={{ 
                                  marginLeft: '0.5rem',
                                  fontSize: '0.8rem',
                                  color: '#2563eb',
                                  fontWeight: '500'
                                }}>
                                  (transfer - receiving)
                                </span>
                              </div>
                            )
                          })()}
                        </div>
                      )}
                    </div>
                  )
                  
                  if (newBalance < 0 && actualAmount < 0) {
                    return (
                      <div>
                        <span style={{ color: '#e53e3e', fontWeight: '600' }}>
                          ⚠️ Insufficient balance warning!
                        </span>
                        {result}
                      </div>
                    )
                  }
                  
                  return result
                })()}
              </div>
            </div>
          )}

          {/* Show Team field only when category is NOT transfer */}
          {(() => {
            const selectedCategory = categories.find(cat => cat.id === parseInt(formData.category_id))
            return selectedCategory?.category_type !== 'transfer' && (
              <div className="form-group">
                <label className="form-label">Team</label>
                <select
                  className="form-input"
                  value={formData.team_id}
                  onChange={(e) => setFormData({...formData, team_id: e.target.value})}
                >
                  <option value="">Select Team</option>
                  {teams.map(team => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
              </div>
            )
          })()}

          <div className="form-actions">
            <button type="button" className="btn" onClick={closeModal}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {editingTransaction ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default Transactions
