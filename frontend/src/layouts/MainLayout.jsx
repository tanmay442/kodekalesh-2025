import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import '../styles/MainLayout.css';

const MainLayout = ({ children }) => {
    const { user, logout } = useUser();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="main-layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h3 className="logo">LegalInt</h3>
                </div>
                <nav className="sidebar-nav">
                    <NavLink to="/dashboard">Dashboard</NavLink>
                    {/* Add other links as needed */}
                </nav>
                <div className="sidebar-footer">
                    {user && (
                        <div className="user-info">
                            <p><strong>{user.full_name}</strong></p>
                            <p><small>{user.role}</small></p>
                            <p className="user-id-display">
                                <small>ID: {user.user_id}</small>
                            </p>
                        </div>
                    )}
                    <button onClick={handleLogout} className="logout-button">
                        Logout
                    </button>
                </div>
            </aside>
            <main className="content-area">
                {children}
            </main>
        </div>
    );
};

export default MainLayout;
