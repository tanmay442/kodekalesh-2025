import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useUser } from '../context/UserContext';
import CaseList from '../components/CaseList';
import '../styles/Dashboard.css';

const DashboardPage = () => {
    const { user } = useUser();
    const [cases, setCases] = useState([]);
    const [caseName, setCaseName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchCases = async () => {
            try {
                setLoading(true);
                const casesRes = await axios.get('/api/cases');
                setCases(casesRes.data);
            } catch (err) {
                console.error("Error fetching cases:", err);
                setError('Failed to load cases.');
            } finally {
                setLoading(false);
            }
        };

        fetchCases();
    }, []);

    const handleCreateCase = async (e) => {
        e.preventDefault();
        setError('');
        if (!caseName) {
            setError('Case name is required.');
            return;
        }
        try {
            const response = await axios.post('/api/cases', { case_name: caseName });
            if (response.status === 201) {
                setCaseName('');
                // Refresh cases list
                const casesRes = await axios.get('/api/cases');
                setCases(casesRes.data);
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to create case.');
        }
    };

    if (loading) {
        return <div>Loading cases...</div>;
    }

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Dashboard</h1>
                <p>Welcome back, {user.full_name}.</p>
            </header>

            {['judge', 'advocate'].includes(user.role) && (
                <section className="card">
                    <h2>Create New Case</h2>
                    <form onSubmit={handleCreateCase} className="create-case-form">
                        <input
                            type="text"
                            value={caseName}
                            onChange={(e) => setCaseName(e.target.value)}
                            placeholder="Enter new case name"
                        />
                        <button type="submit">Create Case</button>
                    </form>
                    {error && <p className="error-message">{error}</p>}
                </section>
            )}

            <section className="card">
                <h2>{user.role === 'judge' ? 'Master Case List' : 'My Assigned Cases'}</h2>
                <CaseList cases={cases} />
            </section>
        </div>
    );
};

export default DashboardPage;