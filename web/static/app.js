const { useState, useEffect } = React;

// API base URL
const API_BASE = '/api';

// Main App Component
function App() {
    const [jobs, setJobs] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [filters, setFilters] = useState({
        company: '',
        scope: '',
        source: '',
        search: ''
    });
    const [viewMode, setViewMode] = useState('today'); // 'today' or 'all'

    useEffect(() => {
        loadStats();
        if (viewMode === 'today') {
            loadTodayJobs();
        } else {
            loadAllJobs();
        }
    }, [viewMode, currentPage, filters]);

    const loadStats = async () => {
        try {
            const response = await axios.get(`${API_BASE}/stats`);
            setStats(response.data);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    };

    const loadTodayJobs = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_BASE}/jobs/today`);
            setJobs(response.data);
            setTotalPages(1);
        } catch (error) {
            console.error('Error loading today\'s jobs:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadAllJobs = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                page: currentPage,
                per_page: 20,
                ...filters
            });
            const response = await axios.get(`${API_BASE}/jobs?${params}`);
            setJobs(response.data.jobs);
            setTotalPages(Math.ceil(response.data.total / 20));
        } catch (error) {
            console.error('Error loading jobs:', error);
        } finally {
            setLoading(false);
        }
    };

    const refreshJobs = async () => {
        try {
            await axios.post(`${API_BASE}/refresh`);
            loadStats();
            if (viewMode === 'today') {
                loadTodayJobs();
            } else {
                loadAllJobs();
            }
        } catch (error) {
            console.error('Error refreshing jobs:', error);
        }
    };

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
        setCurrentPage(1);
    };

    const clearFilters = () => {
        setFilters({ company: '', scope: '', source: '', search: '' });
        setCurrentPage(1);
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const getScopeColor = (scope) => {
        const colors = {
            'Austin': 'bg-blue-100 text-blue-800',
            'US Remote': 'bg-green-100 text-green-800',
            'Unknown': 'bg-gray-100 text-gray-800'
        };
        return colors[scope] || colors['Unknown'];
    };

    const getSourceColor = (source) => {
        const colors = {
            'remotive': 'bg-purple-100 text-purple-800',
            'greenhouse': 'bg-indigo-100 text-indigo-800',
            'lever': 'bg-pink-100 text-pink-800',
            'wwr': 'bg-orange-100 text-orange-800'
        };
        return colors[source] || 'bg-gray-100 text-gray-800';
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Job Checker Dashboard</h1>
                            <p className="text-gray-600">Track your job opportunities</p>
                        </div>
                        <div className="flex space-x-3">
                            <button
                                onClick={refreshJobs}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
                            >
                                <i className="fas fa-sync-alt"></i>
                                <span>Refresh Jobs</span>
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Stats Section */}
            {stats && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <div className="p-2 bg-blue-100 rounded-lg">
                                    <i className="fas fa-briefcase text-blue-600 text-xl"></i>
                                </div>
                                <div className="ml-4">
                                    <p className="text-sm font-medium text-gray-600">Total Jobs</p>
                                    <p className="text-2xl font-semibold text-gray-900">{stats.total_jobs.toLocaleString()}</p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <div className="p-2 bg-green-100 rounded-lg">
                                    <i className="fas fa-calendar-day text-green-600 text-xl"></i>
                                </div>
                                <div className="ml-4">
                                    <p className="text-sm font-medium text-gray-600">Jobs Today</p>
                                    <p className="text-2xl font-semibold text-gray-900">{stats.jobs_today}</p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <div className="p-2 bg-purple-100 rounded-lg">
                                    <i className="fas fa-building text-purple-600 text-xl"></i>
                                </div>
                                <div className="ml-4">
                                    <p className="text-sm font-medium text-gray-600">Top Company</p>
                                    <p className="text-2xl font-semibold text-gray-900">
                                        {Object.keys(stats.jobs_by_company)[0] || 'N/A'}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <div className="p-2 bg-orange-100 rounded-lg">
                                    <i className="fas fa-rss text-orange-600 text-xl"></i>
                                </div>
                                <div className="ml-4">
                                    <p className="text-sm font-medium text-gray-600">Top Source</p>
                                    <p className="text-2xl font-semibold text-gray-900">
                                        {Object.keys(stats.jobs_by_scope)[0] || 'N/A'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Controls */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
                        <div className="flex space-x-4">
                            <button
                                onClick={() => setViewMode('today')}
                                className={`px-4 py-2 rounded-lg font-medium ${
                                    viewMode === 'today'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            >
                                Today's Jobs
                            </button>
                            <button
                                onClick={() => setViewMode('all')}
                                className={`px-4 py-2 rounded-lg font-medium ${
                                    viewMode === 'all'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            >
                                All Jobs
                            </button>
                        </div>
                        
                        {viewMode === 'all' && (
                            <div className="flex flex-wrap gap-3">
                                <input
                                    type="text"
                                    placeholder="Search jobs..."
                                    value={filters.search}
                                    onChange={(e) => handleFilterChange('search', e.target.value)}
                                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <select
                                    value={filters.company}
                                    onChange={(e) => handleFilterChange('company', e.target.value)}
                                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">All Companies</option>
                                    {stats && Object.keys(stats.jobs_by_company).map(company => (
                                        <option key={company} value={company}>{company}</option>
                                    ))}
                                </select>
                                <select
                                    value={filters.source}
                                    onChange={(e) => handleFilterChange('source', e.target.value)}
                                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">All Sources</option>
                                    {stats && Object.keys(stats.jobs_by_scope).map(source => (
                                        <option key={source} value={source}>{source}</option>
                                    ))}
                                </select>
                                <button
                                    onClick={clearFilters}
                                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                                >
                                    Clear
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Jobs List */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="bg-white rounded-lg shadow">
                    {loading ? (
                        <div className="p-8 text-center">
                            <i className="fas fa-spinner fa-spin text-2xl text-gray-400"></i>
                            <p className="mt-2 text-gray-600">Loading jobs...</p>
                        </div>
                    ) : jobs.length === 0 ? (
                        <div className="p-8 text-center">
                            <i className="fas fa-inbox text-4xl text-gray-300"></i>
                            <p className="mt-2 text-gray-600">No jobs found</p>
                        </div>
                    ) : (
                        <>
                            <div className="px-6 py-4 border-b border-gray-200">
                                <h2 className="text-lg font-medium text-gray-900">
                                    {viewMode === 'today' ? 'Today\'s Jobs' : 'All Jobs'} ({jobs.length})
                                </h2>
                            </div>
                            <div className="divide-y divide-gray-200">
                                {jobs.map((job) => (
                                    <div key={job.id} className="p-6 hover:bg-gray-50 transition-colors">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-3 mb-2">
                                                    <h3 className="text-lg font-medium text-gray-900">
                                                        <a 
                                                            href={job.url} 
                                                            target="_blank" 
                                                            rel="noopener noreferrer"
                                                            className="hover:text-blue-600 transition-colors"
                                                        >
                                                            {job.title}
                                                        </a>
                                                    </h3>
                                                    {job.is_stretch && (
                                                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                                                            Stretch
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                                                    <span className="flex items-center">
                                                        <i className="fas fa-building mr-2"></i>
                                                        {job.company}
                                                    </span>
                                                    <span className="flex items-center">
                                                        <i className="fas fa-map-marker-alt mr-2"></i>
                                                        {job.location}
                                                    </span>
                                                    <span className="flex items-center">
                                                        <i className="fas fa-clock mr-2"></i>
                                                        {formatDate(job.created_at)}
                                                    </span>
                                                </div>
                                                <div className="flex items-center space-x-3">
                                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getScopeColor(job.scope)}`}>
                                                        {job.scope}
                                                    </span>
                                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSourceColor(job.source)}`}>
                                                        {job.source}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            
                            {/* Pagination */}
                            {viewMode === 'all' && totalPages > 1 && (
                                <div className="px-6 py-4 border-t border-gray-200">
                                    <div className="flex items-center justify-between">
                                        <div className="text-sm text-gray-700">
                                            Page {currentPage} of {totalPages}
                                        </div>
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                                disabled={currentPage === 1}
                                                className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                                            >
                                                Previous
                                            </button>
                                            <button
                                                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                                disabled={currentPage === totalPages}
                                                className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                                            >
                                                Next
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));
