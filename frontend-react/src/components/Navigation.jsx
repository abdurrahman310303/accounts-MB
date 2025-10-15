import { Link, useLocation } from 'react-router-dom'

function Navigation() {
  const location = useLocation()
  
  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/accounts', label: 'Accounts' },
    { path: '/transactions', label: 'Transactions' },
    { path: '/categories', label: 'Categories' },
    { path: '/teams', label: 'Teams' }
  ]

  return (
    <nav className="nav">
      <div className="container">
        <div className="flex-between">
          <Link to="/" className="nav-brand">
            Finance Tracker
          </Link>
          <ul className="nav-menu">
            {navItems.map(item => (
              <li key={item.path}>
                <Link 
                  to={item.path} 
                  className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
