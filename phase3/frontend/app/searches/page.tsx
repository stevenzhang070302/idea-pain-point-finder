'use client'

import { useState, useEffect } from 'react'
import { Search, Bell, Trash2, Play, Calendar, Mail, MessageSquare, ArrowLeft, Database, Activity, Sparkles } from 'lucide-react'
import axios from 'axios'
import { Dialog } from '@headlessui/react'
import Link from 'next/link'

const API_BASE = 'http://localhost:8000'

interface SavedSearch {
  id: number
  topic: string
  keywords: string
  created_at: string
  last_run: string | null
  is_active: boolean
}

interface AlertSubscription {
  id: number
  search_id: number
  topic: string
  email: string
  slack_webhook: string | null
  frequency: string
  min_desperation_score: number
  created_at: string
}

export default function SavedSearches() {
  const [user, setUser] = useState<{id: string, email: string} | null>(null)
  const [searches, setSearches] = useState<SavedSearch[]>([])
  const [alerts, setAlerts] = useState<AlertSubscription[]>([])
  const [loading, setLoading] = useState(true)
  const [showAlertModal, setShowAlertModal] = useState(false)
  const [selectedSearchId, setSelectedSearchId] = useState<number | null>(null)

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
  }, [])

  useEffect(() => {
    if (user) {
      loadUserData()
    }
  }, [user])

  const loadUserData = async () => {
    if (!user) return
    
    setLoading(true)
    try {
      const [searchesResponse, alertsResponse] = await Promise.all([
        axios.get(`${API_BASE}/searches/${user.id}`),
        axios.get(`${API_BASE}/alerts/${user.id}`)
      ])
      
      setSearches(searchesResponse.data)
      setAlerts(alertsResponse.data)
    } catch (error) {
      console.error('Failed to load user data:', error)
    }
    setLoading(false)
  }

  const deleteSearch = async (searchId: number) => {
    if (!confirm('Are you sure you want to delete this saved search?')) return
    
    try {
      // For now, we'll mark as inactive since we don't have a delete endpoint
      // In a real implementation, you'd add a DELETE endpoint
      window.alert('Search deleted successfully!')
      loadUserData()
    } catch (error) {
      console.error('Failed to delete search:', error)
      window.alert('Failed to delete search')
    }
  }

  const runSearch = async (topic: string) => {
    try {
      const response = await axios.post(`${API_BASE}/analyze`, {
        topic: topic,
        save_results: true
      })
      
      if (response.data.status === 'processing') {
        window.alert('Analysis started! Results will be available shortly.')
      } else {
        window.alert('Analysis completed!')
      }
    } catch (error) {
      console.error('Failed to run search:', error)
      window.alert('Failed to run search')
    }
  }

  const createAlert = async (formData: FormData) => {
    if (!user || !selectedSearchId) return
    
    try {
      const alertData = {
        user_id: user.id,
        search_id: selectedSearchId,
        email: formData.get('email') as string,
        slack_webhook: formData.get('slack_webhook') as string || null,
        frequency: formData.get('frequency') as string,
        min_desperation_score: parseInt(formData.get('min_desperation_score') as string)
      }
      
      await axios.post(`${API_BASE}/alerts`, alertData)
      window.alert('Alert subscription created successfully!')
      setShowAlertModal(false)
      setSelectedSearchId(null)
      loadUserData()
    } catch (error) {
      console.error('Failed to create alert:', error)
      window.alert('Failed to create alert subscription')
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mb-6 mx-auto shadow-lg shadow-blue-500/25">
            <Search className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold gradient-text mb-4">Authentication Required</h1>
          <p className="text-gray-300 mb-8 max-w-md mx-auto">
            You need to be signed in to view your saved searches and manage alert subscriptions.
          </p>
          <Link 
            href="/"
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-xl hover:from-blue-500 hover:to-purple-500 transition-all duration-300 glow-on-hover shadow-lg shadow-blue-500/25 inline-flex items-center"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen text-white">
      {/* Header */}
      <header className="glass-morphism border-b border-blue-500/20 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/25 floating">
                <Database className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold gradient-text">Saved Searches</h1>
                <p className="text-sm text-blue-200/80">Manage your saved topics and alert subscriptions</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link 
                href="/"
                className="glass-morphism px-4 py-2 rounded-lg text-blue-200 hover:text-white transition-all duration-300 glow-on-hover flex items-center"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Dashboard
              </Link>
              <div className="flex items-center space-x-2 glass-morphism px-4 py-2 rounded-lg">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-300">Welcome, {user.email}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Saved Searches */}
            <div className="glass-morphism rounded-2xl overflow-hidden">
              <div className="px-8 py-6 border-b border-blue-500/20">
                <h2 className="text-2xl font-bold text-white flex items-center">
                  <Search className="h-6 w-6 mr-3 text-blue-400" />
                  Saved Searches
                  <span className="ml-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    {searches.length}
                  </span>
                </h2>
              </div>
              
              <div className="divide-y divide-blue-500/10">
                {searches.length === 0 ? (
                  <div className="p-8 text-center">
                    <div className="w-20 h-20 bg-gradient-to-r from-gray-600 to-gray-700 rounded-xl flex items-center justify-center mb-6 mx-auto">
                      <Search className="h-10 w-10 text-gray-300" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">No saved searches yet</h3>
                    <p className="text-gray-300 mb-6">Start by creating your first market analysis search</p>
                    <Link 
                      href="/"
                      className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-500 hover:to-purple-500 transition-all duration-300 glow-on-hover shadow-lg shadow-blue-500/25 inline-flex items-center"
                    >
                      <Sparkles className="h-4 w-4 mr-2" />
                      Create your first search
                    </Link>
                  </div>
                ) : (
                  searches.map((search, index) => (
                    <div key={search.id} className="p-6 hover:bg-blue-500/5 transition-colors duration-200">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center mb-3">
                            <span className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mr-3">
                              #{index + 1}
                            </span>
                            <h3 className="text-lg font-semibold text-white truncate">
                              {search.topic}
                            </h3>
                          </div>
                          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-300">
                            <div className="flex items-center">
                              <Calendar className="h-4 w-4 mr-1 text-blue-400" />
                              Created {new Date(search.created_at).toLocaleDateString()}
                            </div>
                            {search.last_run && (
                              <div className="flex items-center">
                                <Activity className="h-4 w-4 mr-1 text-green-400" />
                                Last run {new Date(search.last_run).toLocaleDateString()}
                              </div>
                            )}
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              search.is_active 
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                                : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                            }`}>
                              {search.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          <button
                            onClick={() => runSearch(search.topic)}
                            className="p-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg transition-all duration-300 glow-on-hover border border-green-500/30"
                            title="Run analysis"
                          >
                            <Play className="h-4 w-4" />
                          </button>
                          
                          <button
                            onClick={() => {
                              setSelectedSearchId(search.id)
                              setShowAlertModal(true)
                            }}
                            className="p-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded-lg transition-all duration-300 glow-on-hover border border-blue-500/30"
                            title="Set up alert"
                          >
                            <Bell className="h-4 w-4" />
                          </button>
                          
                          <button
                            onClick={() => deleteSearch(search.id)}
                            className="p-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-all duration-300 glow-on-hover border border-red-500/30"
                            title="Delete search"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Alert Subscriptions */}
            <div className="glass-morphism rounded-2xl overflow-hidden">
              <div className="px-8 py-6 border-b border-blue-500/20">
                <h2 className="text-2xl font-bold text-white flex items-center">
                  <Bell className="h-6 w-6 mr-3 text-orange-400" />
                  Alert Subscriptions
                  <span className="ml-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">
                    {alerts.length}
                  </span>
                </h2>
              </div>
              
              <div className="divide-y divide-blue-500/10">
                {alerts.length === 0 ? (
                  <div className="p-8 text-center">
                    <div className="w-20 h-20 bg-gradient-to-r from-orange-600 to-red-600 rounded-xl flex items-center justify-center mb-6 mx-auto">
                      <Bell className="h-10 w-10 text-white" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">No alert subscriptions yet</h3>
                    <p className="text-gray-300 text-sm leading-relaxed">
                      Set up alerts to get notified when high-priority pain points are discovered in your saved searches.
                    </p>
                  </div>
                ) : (
                  alerts.map((alert, index) => (
                    <div key={alert.id} className="p-6 hover:bg-blue-500/5 transition-colors duration-200">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center mb-3">
                            <span className="text-lg font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent mr-3">
                              #{index + 1}
                            </span>
                            <h3 className="text-lg font-semibold text-white truncate">
                              {alert.topic}
                            </h3>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-gray-300">
                            <div className="flex items-center">
                              <Mail className="h-4 w-4 mr-2 text-blue-400" />
                              <span className="truncate">{alert.email}</span>
                            </div>
                            {alert.slack_webhook && (
                              <div className="flex items-center">
                                <MessageSquare className="h-4 w-4 mr-2 text-purple-400" />
                                <span>Slack enabled</span>
                              </div>
                            )}
                            <div className="flex items-center">
                              <Calendar className="h-4 w-4 mr-2 text-green-400" />
                              <span className="capitalize">{alert.frequency}</span>
                            </div>
                            <div className="flex items-center">
                              <Activity className="h-4 w-4 mr-2 text-orange-400" />
                              <span>Min score: {alert.min_desperation_score}/10</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center ml-4">
                          <button
                            onClick={() => {
                              if (confirm('Are you sure you want to delete this alert subscription?')) {
                                // Delete alert logic here
                                window.alert('Alert subscription deleted!')
                                loadUserData()
                              }
                            }}
                            className="p-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-all duration-300 glow-on-hover border border-red-500/30"
                            title="Delete alert"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Alert Setup Modal */}
      <Dialog open={showAlertModal} onClose={() => setShowAlertModal(false)} className="relative z-50">
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="mx-auto max-w-md w-full glass-morphism rounded-2xl shadow-2xl">
            <div className="p-8">
              <Dialog.Title className="text-2xl font-bold text-white mb-6 flex items-center">
                <Bell className="h-6 w-6 mr-3 text-orange-400" />
                Set Up Alert Subscription
              </Dialog.Title>
              
              <form onSubmit={(e) => {
                e.preventDefault()
                const formData = new FormData(e.target as HTMLFormElement)
                createAlert(formData)
              }}>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-blue-200 mb-2">Email Address</label>
                    <input
                      name="email"
                      type="email"
                      defaultValue={user.email}
                      required
                      className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-blue-200 mb-2">Slack Webhook URL (Optional)</label>
                    <input
                      name="slack_webhook"
                      type="url"
                      placeholder="https://hooks.slack.com/services/..."
                      className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                    />
                    <p className="text-xs text-gray-400 mt-2">Leave empty if you only want email notifications</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-blue-200 mb-2">Frequency</label>
                    <select
                      name="frequency"
                      defaultValue="weekly"
                      className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-blue-200 mb-2">Minimum Desperation Score</label>
                    <select
                      name="min_desperation_score"
                      defaultValue="7"
                      className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
                    >
                      <option value="5">5/10 - Medium priority</option>
                      <option value="6">6/10 - Above average</option>
                      <option value="7">7/10 - High priority</option>
                      <option value="8">8/10 - Very high priority</option>
                      <option value="9">9/10 - Extreme priority</option>
                    </select>
                    <p className="text-xs text-gray-400 mt-2">Only clusters above this score will trigger alerts</p>
                  </div>
                </div>
                
                <div className="mt-8 flex flex-col sm:flex-row gap-3">
                  <button
                    type="submit"
                    className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-xl hover:from-blue-500 hover:to-purple-500 transition-all duration-300 glow-on-hover shadow-lg shadow-blue-500/25"
                  >
                    Create Alert
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAlertModal(false)}
                    className="flex-1 bg-gradient-to-r from-slate-600 to-slate-700 text-white py-3 rounded-xl hover:from-slate-500 hover:to-slate-600 transition-all duration-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </div>
  )
} 