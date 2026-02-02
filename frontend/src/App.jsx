import React, { useState, useEffect } from 'react';
import axios from 'axios';
import yaml from 'js-yaml';
import ini from 'ini';
import { presentResource } from './presenter';
import './App.css';

// --- Pluralization and Scoping for URL Generation ---
const RESOURCE_URL_MAP = {
    'pod': { path: 'pods', namespaced: true },
    'configmap': { path: 'configmaps', namespaced: true },
    'secret': { path: 'secrets', namespaced: true },
    'service': { path: 'services', namespaced: true },
    'persistentvolumeclaim': { path: 'persistentvolumeclaims', namespaced: true },
    'deployment': { path: 'deployments', namespaced: true },
    'statefulset': { path: 'statefulsets', namespaced: true },
    'daemonset': { path: 'daemonsets', namespaced: true },
    'job': { path: 'jobs', namespaced: true },
    'cronjob': { path: 'cronjobs', namespaced: true },
    'ingress': { path: 'ingresses', namespaced: true },
    'networkpolicy': { path: 'networkpolicies', namespaced: true },
    'horizontalpodautoscaler': { path: 'horizontalpodautoscalers', namespaced: true },
    'persistentvolume': { path: 'persistentvolumes', namespaced: false },
    'customresourcedefinition': { path: 'customresourcedefinitions', namespaced: false },
};

function generateLink(resource, clusterConfigs) {
    const clusterConfig = clusterConfigs.find(c => c.name === resource.cluster_name);
    if (!clusterConfig || !clusterConfig.fqdn) {
        return null;
    }

    // Sanitize the FQDN to remove any existing protocol to prevent invalid URLs
    const sanitizedFqdn = clusterConfig.fqdn.replace(/^(https?:\/\/)?/i, '');

    const resourceTypeLower = resource.resource_type.toLowerCase();
    const mapping = RESOURCE_URL_MAP[resourceTypeLower];

    if (!mapping) {
        return null; // Cannot generate link for unknown resource types
    }

    if (mapping.namespaced) {
        return `https://${sanitizedFqdn}/k8s/ns/${resource.namespace}/${mapping.path}/${resource.resource_name}`;
    } else {
        // Handle cluster-scoped resources
        return `https://${sanitizedFqdn}/k8s/cluster/${mapping.path}/${resource.resource_name}`;
    }
}


const SearchForm = ({ onSearch, loading, filters }) => {
  const [params, setParams] = useState({
    keyword: '',
    cluster_name: '',
    namespace: '',
    resource_type: '',
    resource_name: '',
    limit: 100,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setParams(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(params);
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-row">
        <input
          type="text"
          name="keyword"
          placeholder="Keyword to search"
          value={params.keyword}
          onChange={handleChange}
          className="search-keyword-input"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      <div className="form-row">
        <select name="cluster_name" value={params.cluster_name} onChange={handleChange}>
          <option value="">All Clusters</option>
          {filters.cluster_names.map(name => <option key={name} value={name}>{name}</option>)}
        </select>
        <select name="namespace" value={params.namespace} onChange={handleChange}>
          <option value="">All Namespaces</option>
          {filters.namespaces.map(name => <option key={name} value={name}>{name}</option>)}
        </select>
        <select name="resource_type" value={params.resource_type} onChange={handleChange}>
          <option value="">All Resource Types</option>
          {filters.resource_types.map(name => <option key={name} value={name}>{name}</option>)}
        </select>
        <input
          type="text"
          name="resource_name"
          placeholder="Resource Name (Optional)"
          value={params.resource_name}
          onChange={handleChange}
        />
        <input
          type="number"
          name="limit"
          value={params.limit}
          onChange={handleChange}
          className="limit-input"
        />
      </div>
    </form>
  );
};

const Highlight = ({ text, keyword }) => {
    if (!keyword || !text) return text;
    const regex = new RegExp(`(${keyword})`, 'gi');
    return text.split(regex).map((part, index) =>
      regex.test(part) ? <span key={index} className="highlight">{part}</span> : part
    );
};

const Snippet = ({ text, keyword, contextLines = 5 }) => {
    const lines = text.split('\n');
    const lineIndicesToShow = new Set();

    if (!keyword) return <pre>{text}</pre>;

    lines.forEach((line, i) => {
        if (line.toLowerCase().includes(keyword.toLowerCase())) {
            const start = Math.max(0, i - contextLines);
            const end = Math.min(lines.length, i + contextLines + 1);
            for (let j = start; j < end; j++) {
                lineIndicesToShow.add(j);
            }
        }
    });

    if (lineIndicesToShow.size === 0) return <pre>{text}</pre>;

    const sortedIndices = Array.from(lineIndicesToShow).sort((a, b) => a - b);

    return (
        <div className="snippet-container">
            {sortedIndices.map(index => (
                <div key={index} className="snippet-line">
                    <span className="line-number">{index + 1}</span>
                    <span className="line-text"><Highlight text={lines[index]} keyword={keyword} /></span>
                </div>
            ))}
        </div>
    );
};

const ValueRenderer = ({ value }) => {
    if (typeof value === 'object' && value !== null) {
        return <pre>{JSON.stringify(value, null, 2)}</pre>;
    }
    return String(value);
};

const ConfigMapSummary = ({ data, keyword }) => {
    let filteredData = data;
    if (keyword) {
        filteredData = Object.entries(data).reduce((acc, [key, value]) => {
            if (key.toLowerCase().includes(keyword.toLowerCase()) || (typeof value === 'string' && value.toLowerCase().includes(keyword.toLowerCase()))) {
                acc[key] = value;
            }
            return acc;
        }, {});
    }

    return (
        <div className="key-value-table">
            {Object.entries(filteredData).map(([key, value]) => (
                <div className="kv-row" key={key}>
                    <div className="kv-key"><Highlight text={key} keyword={keyword} /></div>
                    <div className="kv-value">
                        {typeof value === 'string' && value.includes('\n') ? (
                            <Snippet text={value} keyword={keyword} />
                        ) : (
                            <Highlight text={String(value)} keyword={keyword} />
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
};


const StandardSummary = ({ data, fullResourceString, keyword }) => {
    return (
        <>
            <div className="key-value-table">
                {Object.entries(data).map(([key, value]) => (
                    <div className="kv-row" key={key}>
                        <div className="kv-key">{key}</div>
                        <div className="kv-value"><ValueRenderer value={value} /></div>
                    </div>
                ))}
            </div>
            {keyword && (
                <div className="matches-section">
                    <h4>Matches</h4>
                    <Snippet text={fullResourceString} keyword={keyword} />
                </div>
            )}
        </>
    );
};

const ResourceCard = ({ resource, keyword, clusterConfigs }) => {
  const [activeTab, setActiveTab] = useState('summary');
  const summaryData = presentResource(resource);
  const isConfigMap = resource.resource_type?.toLowerCase() === 'configmap';
  const fullResourceString = JSON.stringify(resource.data, null, 2);
  const resourceLink = generateLink(resource, clusterConfigs);

  const resourceTitle = resourceLink ? (
    <a href={resourceLink} target="_blank" rel="noopener noreferrer">
      <Highlight text={resource.resource_name} keyword={keyword} />
    </a>
  ) : (
    <Highlight text={resource.resource_name} keyword={keyword} />
  );

  return (
    <div className="resource-card">
      <h3>{resourceTitle} (<Highlight text={resource.resource_type} keyword={keyword} />)</h3>
      <p>
        <strong>Cluster:</strong> <Highlight text={resource.cluster_name} keyword={keyword} /> | <strong>Namespace:</strong> <Highlight text={resource.namespace} keyword={keyword} />
      </p>
      <div className="tab-buttons">
        <button className={activeTab === 'summary' ? 'active' : ''} onClick={() => setActiveTab('summary')}>Summary</button>
        <button className={activeTab === 'raw' ? 'active' : ''} onClick={() => setActiveTab('raw')}>Raw Data</button>
      </div>
      <div className="tab-content">
        {activeTab === 'summary' ? (
            isConfigMap ? (
                <ConfigMapSummary data={summaryData} keyword={keyword} />
            ) : (
                <StandardSummary data={summaryData} fullResourceString={fullResourceString} keyword={keyword} />
            )
        ) : (
            <div className="code-block">
                <pre><code><Highlight text={fullResourceString} keyword={keyword} /></code></pre>
            </div>
        )}
      </div>
    </div>
  );
};

const Results = ({ results, keyword, hasSearched, clusterConfigs }) => {
  if (!hasSearched) {
    return null;
  }
  if (results.length === 0) {
    return <p>No results found for your query.</p>;
  }
  return (
    <div className="results-container">
      {results.map(res => <ResourceCard key={res.id} resource={res} keyword={keyword} clusterConfigs={clusterConfigs} />)}
    </div>
  );
};

function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ cluster_names: [], namespaces: [], resource_types: [] });
  const [clusterConfigs, setClusterConfigs] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [clusters, namespaces, types, configs] = await Promise.all([
          axios.get('/filters/cluster_names'),
          axios.get('/filters/namespaces'),
          axios.get('/filters/resource_types'),
          axios.get('/api/config'),
        ]);
        setFilters({
          cluster_names: clusters.data,
          namespaces: namespaces.data,
          resource_types: types.data,
        });
        setClusterConfigs(configs.data);
      } catch (err) {
        console.error("Failed to load initial data", err);
      }
    };
    fetchInitialData();
  }, []);

  const handleSearch = async (params) => {
    setLoading(true);
    setError('');
    setHasSearched(true);
    setSearchKeyword(params.keyword);
    try {
      const response = await axios.get('/api/resources', { params });
      setResults(response.data);
    } catch (err) {
      setError('Failed to fetch results. Please try again.');
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>Odin (OKD Resource Inspector)</h1>
      <SearchForm onSearch={handleSearch} loading={loading} filters={filters} />
      {error && <p className="error-message">{error}</p>}
      <Results results={results} keyword={searchKeyword} hasSearched={hasSearched} clusterConfigs={clusterConfigs} />
      <footer className="footer">
        Powered by SRE |
        <a href="https://gitlab.snapp.ir/sre" target="_blank" rel="noopener noreferrer"> GitLab</a> |
        <a href="https://confluence.snapp.ir/x/GAQLBQ" target="_blank" rel="noopener noreferrer"> Confluence</a>
      </footer>
    </div>
  );
}

export default App;
