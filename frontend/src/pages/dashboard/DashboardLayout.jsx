import React, { useContext } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import UserDashboard from './UserDashboard';
import AdminDashboard from './AdminDashboard';
import { AuthContext } from '../../context/authContext';

const DashboardLayout = () => {
  const { user } = useContext(AuthContext);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const renderDashboard = () => {
    switch (user?.role) {
      case 'admin':
        return <AdminDashboard />;
      case 'customer':
        return <UserDashboard />;
      default:
        return <Navigate to="/login" replace />;
    }
  };

  return (
    <div className='container mx-auto flex flex-col md:flex-row gap-4 items-start justify-start'>
      <header key={user.role} className='lg:w-1/5 sm:w-2/5 w-full border border-gray-200'>
        {renderDashboard()}
      </header>
      <main className='p-8 bg-white w-full border border-gray-200 mt-5'>
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;
