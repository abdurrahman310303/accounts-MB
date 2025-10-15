import { useState, useEffect } from 'react'
import Modal from '../components/Modal'
import { categoryAPI } from '../services/api'

function Categories() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [editingCategory, setEditingCategory] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    category_type: 'income',
    description: ''
  })

  const categoryTypes = [
    { value: 'income', label: 'Income' },
    { value: 'expense', label: 'Expense' }
  ]

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await categoryAPI.getAll()
      setCategories(data)
    } catch (err) {
      setError('Failed to load categories')
      console.error('Categories error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openModal = (category = null) => {
    if (category) {
      setEditingCategory(category)
      setFormData({
        name: category.name,
        category_type: category.category_type,
        description: category.description || ''
      })
    } else {
      setEditingCategory(null)
      setFormData({
        name: '',
        category_type: 'income',
        description: ''
      })
    }
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingCategory(null)
    setFormData({
      name: '',
      category_type: 'income',
      description: ''
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingCategory) {
        await categoryAPI.update(editingCategory.id, formData)
      } else {
        await categoryAPI.create(formData)
      }
      closeModal()
      loadCategories()
    } catch (err) {
      setError(`Failed to ${editingCategory ? 'update' : 'create'} category`)
      console.error('Category save error:', err)
    }
  }

  const handleDelete = async (category) => {
    if (window.confirm(`Are you sure you want to delete "${category.name}"?`)) {
      try {
        await categoryAPI.delete(category.id)
        loadCategories()
      } catch (err) {
        setError('Failed to delete category')
        console.error('Category delete error:', err)
      }
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading categories...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Categories</h1>
        <button className="btn btn-primary" onClick={() => openModal()}>
          Add Category
        </button>
      </div>

      {error && (
        <div className="error">
          <p>{error}</p>
        </div>
      )}

      {categories.length > 0 ? (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((category) => (
                <tr key={category.id}>
                  <td>
                    <strong>{category.name}</strong>
                  </td>
                  <td>
                    <span 
                      className={`badge ${category.category_type === 'income' ? 'badge-success' : 'badge-danger'}`}
                      style={{textTransform: 'capitalize'}}
                    >
                      {category.category_type}
                    </span>
                  </td>
                  <td>{category.description || 'No description'}</td>
                  <td>
                    <button 
                      className="btn btn-small"
                      onClick={() => openModal(category)}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-small"
                      onClick={() => handleDelete(category)}
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
          <p>No categories found.</p>
          <button className="btn btn-primary" onClick={() => openModal()}>
            Create your first category
          </button>
        </div>
      )}

      <Modal 
        isOpen={showModal} 
        onClose={closeModal}
        title={editingCategory ? 'Edit Category' : 'Add Category'}
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
            <label className="form-label">Type</label>
            <select
              className="form-input"
              value={formData.category_type}
              onChange={(e) => setFormData({...formData, category_type: e.target.value})}
              required
            >
              {categoryTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-input"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows={3}
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn" onClick={closeModal}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {editingCategory ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default Categories
