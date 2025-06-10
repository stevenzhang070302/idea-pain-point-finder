'use client'

import { useState, useEffect } from 'react'
import { Search, Download, TrendingUp, AlertTriangle, Users, Calendar, Bell, Save, Zap, Target, Rocket, Brain, Activity, Sparkles } from 'lucide-react'
import axios from 'axios'
import { Dialog } from '@headlessui/react'
import { Scatter, ScatterChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import Link from 'next/link'

const API_BASE = 'http://localhost:8000'

interface Cluster {
  cluster_id: string
  topic: string
  problem_category: string
  frequency: number
  desperation_score: number
  avg_pain_score: number
  avg_upvotes: number
  total_engagement_weight: number
  trend_tag: string
  market_proxy: {
    subscribers: number
    posts_per_week: number
  }
  sample_post: {
    title: string
    url: string
    content?: string
  }
  mvp_suggestion: string
  all_subreddits: string[]
  related_pain_points: Array<{
    summary: string
    pain_score: number
    subreddit: string
    engagement_weight: number
  }>
}

interface AnalysisResults {
  topic: string
  analysis_summary: {
    total_clusters: number
    total_posts: number
    average_desperation_score: number
    high_priority_clusters: number
    total_engagement_weight: number
    trending_clusters: number
  }
  clusters: Cluster[]
}

export default function Dashboard() {
  const [searchTopic, setSearchTopic] = useState('')
  const [results, setResults] = useState<AnalysisResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedCluster, setSelectedCluster] = useState<Cluster | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [user, setUser] = useState<{id: string, email: string} | null>(null)
  const [showAuth, setShowAuth] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')

  // Authentication state
  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const handleAuth = async (email: string, password: string) => {
    try {
      const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register'
      const response = await axios.post(`${API_BASE}${endpoint}`, { email, password })
      
      const userData = { id: response.data.user_id, email }
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
      setShowAuth(false)
    } catch (error) {
      console.error('Authentication failed:', error)
      alert('Authentication failed. Please try again.')
    }
  }

  const handleSearch = async () => {
    if (!searchTopic.trim()) return
    
    setLoading(true)
    try {
      // Start analysis
      const response = await axios.post(`${API_BASE}/analyze`, {
        topic: searchTopic,
        save_results: true
      })
      
      if (response.data.status === 'completed') {
        setResults(response.data.results)
      } else {
        // Poll for results
        const topicHash = response.data.id
        let attempts = 0
        const maxAttempts = 60 // 5 minutes max
        
        const pollResults = async () => {
          try {
            const statusResponse = await axios.get(`${API_BASE}/analyze/${topicHash}`)
            if (statusResponse.data.status === 'completed') {
              setResults(statusResponse.data.results)
              setLoading(false)
            } else if (attempts < maxAttempts) {
              attempts++
              setTimeout(pollResults, 5000) // Poll every 5 seconds
            } else {
              setLoading(false)
              alert('Analysis timed out. Please try again.')
            }
          } catch (error) {
            console.error('Error polling results:', error)
            setLoading(false)
          }
        }
        
        setTimeout(pollResults, 5000)
      }
    } catch (error) {
      console.error('Search failed:', error)
      setLoading(false)
      alert('Search failed. Please try again.')
    }
  }

  const handleSaveSearch = async () => {
    if (!user || !searchTopic.trim()) return
    
    try {
      await axios.post(`${API_BASE}/searches`, {
        user_id: user.id,
        topic: searchTopic,
        keywords: ''
      })
      alert('Search saved successfully!')
    } catch (error) {
      console.error('Failed to save search:', error)
    }
  }

  const exportToCsv = async () => {
    if (!results) return
    
    try {
      const response = await axios.get(`${API_BASE}/topics/${results.topic}/export.csv`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `pain_analysis_${results.topic.replace(' ', '_')}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const openClusterModal = (cluster: Cluster) => {
    setSelectedCluster(cluster)
    setIsModalOpen(true)
  }

  // Prepare heatmap data
  const heatmapData = results?.clusters.map(cluster => ({
    desperation: cluster.desperation_score,
    engagement: cluster.total_engagement_weight,
    frequency: cluster.frequency,
    name: cluster.cluster_id,
    trending: cluster.trend_tag.includes('🆙')
  })) || []

  return (
    <div className="min-h-screen text-white">
      {/* Header */}
      <header className="glass-morphism border-b border-blue-500/20 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="floating">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <Brain className="h-6 w-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-3xl font-bold gradient-text">Reddit Pain Finder</h1>
                <p className="text-sm text-blue-200/80">AI-Powered Market Intelligence Dashboard</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {user ? (
                <div className="flex items-center space-x-4">
                  <Link 
                    href="/searches"
                    className="glass-morphism px-4 py-2 rounded-lg text-blue-200 hover:text-white transition-all duration-300 glow-on-hover text-sm"
                  >
                    <Save className="h-4 w-4 inline mr-2" />
                    Saved Searches
                  </Link>
                  <div className="flex items-center space-x-2 glass-morphism px-4 py-2 rounded-lg">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-sm text-gray-300">Welcome, {user.email}</span>
                  </div>
                  <button 
                    onClick={() => {
                      setUser(null)
                      localStorage.removeItem('user')
                    }}
                    className="text-sm text-red-400 hover:text-red-300 transition-colors"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowAuth(true)}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-500 hover:to-purple-500 transition-all duration-300 glow-on-hover shadow-lg shadow-blue-500/25"
                >
                  <Zap className="h-4 w-4 inline mr-2" />
                  Get Started
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-12 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-5xl font-bold gradient-text mb-4 floating">
              Discover Hidden Market Opportunities
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Leverage AI to analyze Reddit conversations and uncover pain points that could become your next big business idea
            </p>
          </div>

          {/* Search Section */}
          <div className="glass-morphism rounded-2xl p-8 mb-12 neon-border">
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex-1">
                <label htmlFor="search" className="block text-sm font-medium text-blue-200 mb-3">
                  <Target className="h-4 w-4 inline mr-2" />
                  Enter your target market or niche
                </label>
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    id="search"
                    type="text"
                    value={searchTopic}
                    onChange={(e) => setSearchTopic(e.target.value)}
                    placeholder="e.g., indie game developers, college students, small business owners"
                    className="pl-12 w-full px-4 py-4 bg-slate-800/50 border border-blue-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400 transition-all duration-300"
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl pointer-events-none opacity-0 transition-opacity duration-300 hover:opacity-100"></div>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleSearch}
                  disabled={loading || !searchTopic.trim()}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl hover:from-blue-500 hover:to-purple-500 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-300 glow-on-hover shadow-lg shadow-blue-500/25"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      <span className="hidden sm:inline">Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Rocket className="h-5 w-5 mr-2" />
                      <span className="hidden sm:inline">Analyze Market</span>
                      <span className="sm:hidden">Analyze</span>
                    </>
                  )}
                </button>
                {user && searchTopic && (
                  <button
                    onClick={handleSaveSearch}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-4 rounded-xl hover:from-green-500 hover:to-emerald-500 flex items-center justify-center transition-all duration-300 glow-on-hover shadow-lg shadow-green-500/25"
                  >
                    <Save className="h-5 w-5 mr-2" />
                    <span className="hidden sm:inline">Save</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Results Section */}
      {results && (
        <section className="pb-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <div className="glass-morphism rounded-xl p-6 glow-on-hover floating">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <dt className="text-sm font-medium text-gray-300 truncate">Total Clusters</dt>
                    <dd className="text-2xl font-bold text-white">{results.analysis_summary.total_clusters}</dd>
                  </div>
                </div>
              </div>

              <div className="glass-morphism rounded-xl p-6 glow-on-hover floating" style={{animationDelay: '0.5s'}}>
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-r from-amber-500 to-orange-500 rounded-lg flex items-center justify-center">
                      <Activity className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <dt className="text-sm font-medium text-gray-300 truncate">Avg Desperation</dt>
                    <dd className="text-2xl font-bold text-white">{results.analysis_summary.average_desperation_score.toFixed(1)}/10</dd>
                  </div>
                </div>
              </div>

              <div className="glass-morphism rounded-xl p-6 glow-on-hover floating" style={{animationDelay: '1s'}}>
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                      <Users className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <dt className="text-sm font-medium text-gray-300 truncate">High Priority</dt>
                    <dd className="text-2xl font-bold text-white">{results.analysis_summary.high_priority_clusters}</dd>
                  </div>
                </div>
              </div>

              <div className="glass-morphism rounded-xl p-6 glow-on-hover floating" style={{animationDelay: '1.5s'}}>
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-violet-500 rounded-lg flex items-center justify-center">
                      <TrendingUp className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <dt className="text-sm font-medium text-gray-300 truncate">Trending</dt>
                    <dd className="text-2xl font-bold text-white">{results.analysis_summary.trending_clusters} <Sparkles className="h-4 w-4 inline ml-1" /></dd>
                  </div>
                </div>
              </div>
            </div>

            {/* Heat Map */}
            <div className="glass-morphism rounded-2xl p-8 mb-12">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Market Opportunity Matrix</h2>
                  <p className="text-gray-300">Desperation vs Engagement Analysis</p>
                </div>
                <button
                  onClick={exportToCsv}
                  className="bg-gradient-to-r from-slate-600 to-slate-700 text-white px-6 py-3 rounded-xl hover:from-slate-500 hover:to-slate-600 flex items-center transition-all duration-300 glow-on-hover shadow-lg shadow-slate-500/25"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Data
                </button>
              </div>
              <div className="h-80 bg-slate-900/50 rounded-xl p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart data={heatmapData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(59, 130, 246, 0.2)" />
                    <XAxis 
                      dataKey="desperation" 
                      name="Desperation Score" 
                      domain={[0, 10]} 
                      stroke="#e2e8f0"
                      tick={{ fill: '#e2e8f0' }}
                    />
                    <YAxis 
                      dataKey="engagement" 
                      name="Engagement Weight" 
                      stroke="#e2e8f0"
                      tick={{ fill: '#e2e8f0' }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [value, name]}
                      labelFormatter={(label) => `Cluster: ${label}`}
                      contentStyle={{
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: '8px',
                        color: '#e2e8f0'
                      }}
                    />
                    <Scatter 
                      dataKey="engagement" 
                      fill="url(#blueGradient)"
                    />
                    <defs>
                      <linearGradient id="blueGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#3b82f6" />
                        <stop offset="100%" stopColor="#8b5cf6" />
                      </linearGradient>
                    </defs>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Results Table */}
            <div className="glass-morphism rounded-2xl overflow-hidden">
              <div className="px-8 py-6 border-b border-blue-500/20">
                <h3 className="text-2xl font-bold text-white mb-2">Pain Point Clusters</h3>
                <p className="text-gray-300">
                  Click on any cluster to explore detailed insights and market opportunities
                </p>
              </div>
              <div className="divide-y divide-blue-500/10">
                {results.clusters.map((cluster, index) => (
                  <div key={cluster.cluster_id} className="hover:bg-blue-500/5 transition-colors duration-200">
                    <button
                      onClick={() => openClusterModal(cluster)}
                      className="block w-full text-left px-8 py-6"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center mb-3">
                            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mr-3">
                              #{index + 1}
                            </span>
                            <h4 className="text-lg font-semibold text-white truncate mr-2">
                              {cluster.topic}
                            </h4>
                            {cluster.trend_tag.includes('🆙') && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                                <TrendingUp className="h-3 w-3 mr-1" />
                                Trending
                              </span>
                            )}
                            <span className={`ml-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                              cluster.desperation_score >= 8 ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                              cluster.desperation_score >= 6 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                              'bg-green-500/20 text-green-400 border border-green-500/30'
                            }`}>
                              {cluster.desperation_score}/10
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <div className="flex items-center space-x-6 text-sm text-gray-300">
                              <span className="flex items-center">
                                <Users className="h-4 w-4 mr-1 text-blue-400" />
                                {cluster.frequency} posts
                              </span>
                              <span className="flex items-center">
                                <Activity className="h-4 w-4 mr-1 text-purple-400" />
                                {cluster.market_proxy.subscribers.toLocaleString()} subscribers
                              </span>
                            </div>
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">
                              {cluster.problem_category}
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Cluster Detail Modal */}
      <Dialog open={isModalOpen} onClose={() => setIsModalOpen(false)} className="relative z-50">
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="mx-auto max-w-5xl w-full glass-morphism rounded-2xl shadow-2xl max-h-[90vh] overflow-y-auto">
            {selectedCluster && (
              <div className="p-8">
                <Dialog.Title className="text-2xl font-bold text-white mb-6 flex items-center">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                    <Target className="h-4 w-4 text-white" />
                  </div>
                  {selectedCluster.topic} {selectedCluster.trend_tag}
                </Dialog.Title>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                  <div className="glass-morphism rounded-xl p-6">
                    <h4 className="font-semibold text-white mb-4 flex items-center">
                      <Activity className="h-5 w-5 mr-2 text-blue-400" />
                      Key Metrics
                    </h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-300">Desperation Score:</span>
                        <span className="font-semibold text-red-400">{selectedCluster.desperation_score}/10</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-300">Frequency:</span>
                        <span className="font-semibold text-white">{selectedCluster.frequency} posts</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-300">Avg Upvotes:</span>
                        <span className="font-semibold text-white">{selectedCluster.avg_upvotes}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-300">Engagement Weight:</span>
                        <span className="font-semibold text-white">{selectedCluster.total_engagement_weight.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="glass-morphism rounded-xl p-6">
                    <h4 className="font-semibold text-white mb-4 flex items-center">
                      <Users className="h-5 w-5 mr-2 text-purple-400" />
                      Market Intelligence
                    </h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-300">Subscribers:</span>
                        <span className="font-semibold text-white">{selectedCluster.market_proxy.subscribers.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-300">Posts/Week:</span>
                        <span className="font-semibold text-white">{selectedCluster.market_proxy.posts_per_week}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-300">Category:</span>
                        <span className="font-semibold text-white">{selectedCluster.problem_category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-300">Subreddits:</span>
                        <span className="font-semibold text-white text-right">{selectedCluster.all_subreddits.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="glass-morphism rounded-xl p-6 mb-8">
                  <h4 className="font-semibold text-white mb-4 flex items-center">
                    <Rocket className="h-5 w-5 mr-2 text-green-400" />
                    MVP Opportunity
                  </h4>
                  <p className="text-gray-300 leading-relaxed bg-gradient-to-r from-green-500/10 to-blue-500/10 p-4 rounded-lg border border-green-500/20">
                    {selectedCluster.mvp_suggestion}
                  </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                  <div className="glass-morphism rounded-xl p-6">
                    <h4 className="font-semibold text-white mb-4 flex items-center">
                      <Bell className="h-5 w-5 mr-2 text-orange-400" />
                      Sample Post
                    </h4>
                    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-600/30">
                      <h5 className="font-medium text-white mb-3">{selectedCluster.sample_post.title}</h5>
                      <a 
                        href={selectedCluster.sample_post.url} 
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        View on Reddit →
                      </a>
                    </div>
                  </div>

                  <div className="glass-morphism rounded-xl p-6">
                    <h4 className="font-semibold text-white mb-4 flex items-center">
                      <AlertTriangle className="h-5 w-5 mr-2 text-red-400" />
                      Related Pain Points
                    </h4>
                    <div className="space-y-3 max-h-40 overflow-y-auto">
                      {selectedCluster.related_pain_points.slice(0, 3).map((pain, idx) => (
                        <div key={idx} className="bg-slate-800/30 rounded-lg p-3 border-l-4 border-blue-500/50">
                          <div className="flex justify-between items-start">
                            <div className="flex-1 mr-3">
                              <p className="text-sm text-gray-300 leading-relaxed">{pain.summary}</p>
                              <p className="text-xs text-gray-400 mt-2">r/{pain.subreddit} • Pain Score: {pain.pain_score}/10</p>
                            </div>
                            <span className="text-xs text-blue-400 bg-blue-500/20 px-2 py-1 rounded">
                              {pain.engagement_weight.toFixed(1)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="px-6 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-500 hover:to-slate-600 transition-all duration-300"
                  >
                    Close Analysis
                  </button>
                </div>
              </div>
            )}
          </Dialog.Panel>
        </div>
      </Dialog>

      {/* Auth Modal */}
      <Dialog open={showAuth} onClose={() => setShowAuth(false)} className="relative z-50">
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="mx-auto max-w-md w-full glass-morphism rounded-2xl shadow-2xl">
            <div className="p-8">
              <Dialog.Title className="text-2xl font-bold text-white mb-6 text-center">
                {authMode === 'login' ? 'Welcome Back' : 'Join the Future'}
              </Dialog.Title>
              
              <form onSubmit={(e) => {
                e.preventDefault()
                const formData = new FormData(e.target as HTMLFormElement)
                const email = formData.get('email') as string
                const password = formData.get('password') as string
                handleAuth(email, password)
              }}>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-blue-200 mb-2">Email</label>
                    <input
                      name="email"
                      type="email"
                      required
                      className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                      placeholder="Enter your email"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-blue-200 mb-2">Password</label>
                    <input
                      name="password"
                      type="password"
                      required
                      className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                      placeholder="Enter your password"
                    />
                  </div>
                </div>
                
                <div className="mt-8 flex flex-col space-y-4">
                  <button
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-xl hover:from-blue-500 hover:to-purple-500 transition-all duration-300 glow-on-hover shadow-lg shadow-blue-500/25"
                  >
                    {authMode === 'login' ? 'Sign In' : 'Create Account'}
                  </button>
                  <div className="flex justify-between">
                    <button
                      type="button"
                      onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
                      className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      {authMode === 'login' ? 'Need an account?' : 'Already have an account?'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowAuth(false)}
                      className="text-sm text-gray-400 hover:text-gray-300 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </div>
  )
}
