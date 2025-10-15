import { useState, useEffect } from 'react'
import './MonthFilter.css'

function DashboardFilter({ onFilterChange, accounts = [], teams = [], categories = [] }) {
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    accountId: '',
    teamId: '',
    categoryId: '',
    timeRange: 'all' // all, thisMonth, lastMonth, thisYear, lastYear, custom
  })

  // Generate date options for quick selection
  const getTimeRangeOptions = () => {
    const now = new Date()
    const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0)
    const thisYear = new Date(now.getFullYear(), 0, 1)
    const lastYear = new Date(now.getFullYear() - 1, 0, 1)
    const lastYearEnd = new Date(now.getFullYear() - 1, 11, 31)

    return {
      thisMonth: {
        start: thisMonth.toISOString().split('T')[0],
        end: now.toISOString().split('T')[0]
      },
      lastMonth: {
        start: lastMonth.toISOString().split('T')[0],
        end: lastMonthEnd.toISOString().split('T')[0]
      },
      thisYear: {
        start: thisYear.toISOString().split('T')[0],
        end: now.toISOString().split('T')[0]
      },
      lastYear: {
        start: lastYear.toISOString().split('T')[0],
        end: lastYearEnd.toISOString().split('T')[0]
      }
    }
  }

  const handleTimeRangeChange = (timeRange) => {
    const ranges = getTimeRangeOptions()
    let newFilters = { ...filters, timeRange }

    if (timeRange === 'all') {
      newFilters.startDate = ''
      newFilters.endDate = ''
    } else if (timeRange === 'custom') {
      // Keep current custom dates
    } else if (ranges[timeRange]) {
      newFilters.startDate = ranges[timeRange].start
      newFilters.endDate = ranges[timeRange].end
    }

    setFilters(newFilters)
  }

  const handleFilterChange = (field, value) => {
    const newFilters = { ...filters, [field]: value }
    
    // If changing dates manually, set to custom
    if (field === 'startDate' || field === 'endDate') {
      newFilters.timeRange = 'custom'
    }
    
    setFilters(newFilters)
  }

  const clearFilters = () => {
    const clearedFilters = {
      startDate: '',
      endDate: '',
      accountId: '',
      teamId: '',
      categoryId: '',
      timeRange: 'all'
    }
    setFilters(clearedFilters)
  }

  // Notify parent component when filters change
  useEffect(() => {
    onFilterChange(filters)
  }, [filters, onFilterChange])

  return (
    <div className="dashboard-filters">
      <div className="filter-row">
        <div className="filter-group">
          <label className="filter-label">Time Range:</label>
          <select
            className="filter-select"
            value={filters.timeRange}
            onChange={(e) => handleTimeRangeChange(e.target.value)}
          >
            <option value="all">All Time</option>
            <option value="thisMonth">This Month</option>
            <option value="lastMonth">Last Month</option>
            <option value="thisYear">This Year</option>
            <option value="lastYear">Last Year</option>
            <option value="custom">Custom Range</option>
          </select>
        </div>

        {filters.timeRange === 'custom' && (
          <>
            <div className="filter-group">
              <label className="filter-label">Start Date:</label>
              <input
                type="date"
                className="filter-input"
                value={filters.startDate}
                onChange={(e) => handleFilterChange('startDate', e.target.value)}
              />
            </div>
            <div className="filter-group">
              <label className="filter-label">End Date:</label>
              <input
                type="date"
                className="filter-input"
                value={filters.endDate}
                onChange={(e) => handleFilterChange('endDate', e.target.value)}
              />
            </div>
          </>
        )}

        <div className="filter-group">
          <label className="filter-label">Account:</label>
          <select
            className="filter-select"
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
        </div>

        <div className="filter-group">
          <label className="filter-label">Team:</label>
          <select
            className="filter-select"
            value={filters.teamId}
            onChange={(e) => handleFilterChange('teamId', e.target.value)}
          >
            <option value="">All Teams</option>
            {teams.map(team => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Category:</label>
          <select
            className="filter-select"
            value={filters.categoryId}
            onChange={(e) => handleFilterChange('categoryId', e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.name} ({category.category_type})
              </option>
            ))}
          </select>
        </div>

        <div className="filter-actions">
          <button className="btn btn-secondary" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  )
}

export default DashboardFilter