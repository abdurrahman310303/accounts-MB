import { useState, useEffect } from 'react'
import Modal from '../components/Modal'
import { teamAPI } from '../services/api'

function Teams() {
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [editingTeam, setEditingTeam] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  })

  useEffect(() => {
    loadTeams()
  }, [])

  const loadTeams = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await teamAPI.getAll()
      setTeams(data)
    } catch (err) {
      setError('Failed to load teams')
      console.error('Teams error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openModal = (team = null) => {
    if (team) {
      setEditingTeam(team)
      setFormData({
        name: team.name,
        description: team.description || ''
      })
    } else {
      setEditingTeam(null)
      setFormData({
        name: '',
        description: ''
      })
    }
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingTeam(null)
    setFormData({
      name: '',
      description: ''
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingTeam) {
        await teamAPI.update(editingTeam.id, formData)
      } else {
        await teamAPI.create(formData)
      }
      closeModal()
      loadTeams()
    } catch (err) {
      setError(`Failed to ${editingTeam ? 'update' : 'create'} team`)
      console.error('Team save error:', err)
    }
  }

  const handleDelete = async (team) => {
    if (window.confirm(`Are you sure you want to delete "${team.name}"?`)) {
      try {
        await teamAPI.delete(team.id)
        loadTeams()
      } catch (err) {
        setError('Failed to delete team')
        console.error('Team delete error:', err)
      }
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading teams...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Teams</h1>
        <button className="btn btn-primary" onClick={() => openModal()}>
          Add Team
        </button>
      </div>

      {error && (
        <div className="error">
          <p>{error}</p>
        </div>
      )}

      {teams.length > 0 ? (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team) => (
                <tr key={team.id}>
                  <td>
                    <strong>{team.name}</strong>
                  </td>
                  <td>{team.description || 'No description'}</td>
                  <td>
                    <button 
                      className="btn btn-small"
                      onClick={() => openModal(team)}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-small"
                      onClick={() => handleDelete(team)}
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
          <p>No teams found.</p>
          <button className="btn btn-primary" onClick={() => openModal()}>
            Create your first team
          </button>
        </div>
      )}

      <Modal 
        isOpen={showModal} 
        onClose={closeModal}
        title={editingTeam ? 'Edit Team' : 'Add Team'}
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
              {editingTeam ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default Teams
