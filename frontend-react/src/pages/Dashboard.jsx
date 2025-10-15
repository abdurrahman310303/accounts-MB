import { useState, useEffect, useCallback } from 'react'
import { accountAPI, transactionAPI, categoryAPI, teamAPI, formatCurrency, formatCurrencyCompact } from '../services/api'
import DashboardFilter from '../components/MonthFilter'

function Dashboard() {
  const [stats, setStats] = useState({
    totalCurrentBalance: 0,
    totalIncome: 0,
    totalExpenses: 0,
    profitAndLoss: 0
  })
  const [recentTransactions, setRecentTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Filter-related state
  const [accounts, setAccounts] = useState([])
  const [teams, setTeams] = useState([])
  const [categories, setCategories] = useState([])
  const [currentFilters, setCurrentFilters] = useState({})

  const loadDashboardData = useCallback(async (filters = {}) => {
    try {
      setLoading(true)
      setError(null)

      // Build transaction API parameters based on filters
      const transactionParams = {
        limit: 1000
      }

      // Add filters to transaction params
      if (filters.startDate) transactionParams.start_date = filters.startDate
      if (filters.endDate) transactionParams.end_date = filters.endDate
      if (filters.accountId) transactionParams.account_id = parseInt(filters.accountId)
      if (filters.teamId) transactionParams.team_id = parseInt(filters.teamId)
      if (filters.categoryId) transactionParams.category_id = parseInt(filters.categoryId)

      const [accountsData, transactions, categoriesData, teamsData] = await Promise.all([
        accountAPI.getAll(),
        transactionAPI.getAll(transactionParams),
        categoryAPI.getAll(),
        teamAPI.getAll()
      ])

      // Store filter data for the filter component
      setAccounts(accountsData)
      setCategories(categoriesData)
      setTeams(teamsData)

      // Calculate total current balance
      let totalCurrentBalance = 0
      
      if (filters.accountId) {
        // If filtering by account, only show balance for that account
        const filteredAccount = accountsData.find(acc => acc.id === parseInt(filters.accountId))
        totalCurrentBalance = filteredAccount ? parseFloat(filteredAccount.current_balance) || 0 : 0
      } else {
        // Show total balance for all accounts
        totalCurrentBalance = accountsData.reduce((sum, account) => {
          const balance = parseFloat(account.current_balance) || 0
          return sum + balance
        }, 0)
      }

      console.log('Accounts data:', accountsData)
      console.log('Filtered transactions:', transactions)
      console.log('Total current balance calculated:', totalCurrentBalance)

      // Calculate filtered expenses and income
      const totalExpenses = transactions.reduce((sum, transaction) => {
        if (!transaction.category_id) return sum
        
        const category = categoriesData.find(cat => cat.id === transaction.category_id)
        if (!category) return sum
        
        // Only consider transactions with expense category type as expenses
        const isExpenseCategory = category.category_type === 'expense'
        
        if (!isExpenseCategory) return sum
        
        const amount = parseFloat(transaction.amount) || 0
        return sum + Math.abs(amount)
      }, 0)

      const totalIncome = transactions.reduce((sum, transaction) => {
        if (!transaction.category_id) return sum
        
        const category = categoriesData.find(cat => cat.id === transaction.category_id)
        if (!category) return sum
        
        // Only consider transactions with income category type as income
        const isIncomeCategory = category.category_type === 'income'
        
        if (!isIncomeCategory) return sum
        
        const amount = parseFloat(transaction.amount) || 0
        return sum + Math.abs(amount)
      }, 0)

      const profitAndLoss = totalIncome - totalExpenses

      console.log('Filtered expenses calculated:', totalExpenses)
      console.log('Filtered income calculated:', totalIncome)
      console.log('Filtered profit and loss calculated:', profitAndLoss)

      setStats({
        totalCurrentBalance,
        totalIncome,
        totalExpenses,
        profitAndLoss: profitAndLoss
      })

      setRecentTransactions(transactions.slice(0, 10))
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error('Dashboard error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleFilterChange = useCallback((filters) => {
    setCurrentFilters(filters)
    loadDashboardData(filters)
  }, [loadDashboardData])

  const handleRefresh = () => {
    loadDashboardData(currentFilters)
  }

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  if (loading && accounts.length === 0) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button className="btn" onClick={handleRefresh}>
          Retry
        </button>
      </div>
    )
  }

  // Check if any filters are active
  const isFiltered = Object.keys(currentFilters).some(key => 
    currentFilters[key] && currentFilters[key] !== '' && currentFilters[key] !== 'all'
  )

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <button className="btn" onClick={handleRefresh} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      <DashboardFilter
        onFilterChange={handleFilterChange}
        accounts={accounts}
        teams={teams}
        categories={categories}
      />

      <div className="dashboard-stats">
        <div className={`stat-card ${isFiltered ? 'filtered' : ''}`}>
          <span className="stat-value">{formatCurrencyCompact(stats.totalCurrentBalance, 'PKR')}</span>
          <span className={`stat-label ${isFiltered ? 'filtered' : ''}`}>
            {currentFilters.accountId ? 'Account Balance' : 'Total Current Balance'}
          </span>
          <span className="stat-detail">{formatCurrency(stats.totalCurrentBalance, 'PKR')}</span>
        </div>
        <div className={`stat-card ${isFiltered ? 'filtered' : ''}`}>
          <span className="stat-value" style={{ color: '#38a169', fontWeight: '700' }}>
            {formatCurrencyCompact(stats.totalIncome, 'PKR')}
          </span>
          <span className={`stat-label ${isFiltered ? 'filtered' : ''}`}>
            {isFiltered ? 'Filtered Income' : 'Total Income'}
          </span>
          <span className="stat-detail">{formatCurrency(stats.totalIncome, 'PKR')}</span>
        </div>
        <div className={`stat-card ${isFiltered ? 'filtered' : ''}`}>
          <span className="stat-value" style={{ color: '#e53e3e', fontWeight: '700' }}>
            {formatCurrencyCompact(stats.totalExpenses, 'PKR')}
          </span>
          <span className={`stat-label ${isFiltered ? 'filtered' : ''}`}>
            {isFiltered ? 'Filtered Expenses' : 'Total Expenses'}
          </span>
          <span className="stat-detail">{formatCurrency(stats.totalExpenses, 'PKR')}</span>
        </div>
        <div className={`stat-card ${isFiltered ? 'filtered' : ''}`}>
          <span className="stat-value" style={{ 
            color: stats.profitAndLoss >= 0 ? '#38a169' : '#e53e3e',
            fontWeight: '700'
          }}>
            {stats.profitAndLoss >= 0 ? '+' : ''}{formatCurrencyCompact(stats.profitAndLoss, 'PKR')}
          </span>
          <span className={`stat-label ${isFiltered ? 'filtered' : ''}`}>
            {isFiltered ? 'Filtered P&L' : 'Profit & Loss'}
          </span>
          <span className="stat-detail">{formatCurrency(stats.profitAndLoss, 'PKR')}</span>
        </div>
      </div>

      {recentTransactions.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>
              {isFiltered 
                ? 'Filtered Transactions' 
                : 'Recent Transactions'
              } ({recentTransactions.length} shown)
            </h3>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Category</th>
                  <th>Team</th>
                  <th>Amount</th>
                  <th>Balance After</th>
                </tr>
              </thead>
              <tbody>
                {recentTransactions.map((transaction) => {
                  const category = categories.find(cat => cat.id === transaction.category_id)
                  const team = teams.find(t => t.id === transaction.team_id)
                  
                  return (
                    <tr key={transaction.id}>
                      <td>{new Date(transaction.transaction_date).toLocaleDateString()}</td>
                      <td>{transaction.description || 'No description'}</td>
                      <td>{category ? `${category.name} (${category.category_type})` : 'N/A'}</td>
                      <td>{team ? team.name : 'N/A'}</td>
                      <td className={transaction.amount >= 0 ? 'amount-positive' : 'amount-negative'} style={{
                        color: transaction.amount >= 0 ? '#38a169' : '#e53e3e',
                        fontWeight: '600'
                      }}>
                        {transaction.amount >= 0 ? '+' : ''}{formatCurrency(transaction.amount, transaction.currency || 'PKR')}
                      </td>
                      <td>{formatCurrency(transaction.balance_after, transaction.currency || 'PKR')}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {recentTransactions.length === 0 && !loading && (
        <div className="card text-center">
          <p>
            {isFiltered
              ? 'No transactions found with the current filters. Try adjusting your filter criteria.'
              : 'No transactions found. Start by creating some accounts and transactions.'
            }
          </p>
        </div>
      )}
    </div>
  )
}

export default Dashboard
