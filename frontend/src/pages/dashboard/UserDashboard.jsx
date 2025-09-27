import React, { useContext } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../context/authContext';

const navItems = [
  { path: '/dashboard', label: 'Dashboard' },
  { path: '/dashboard/Profile', label: 'Profile' },
  { path: '/dashboard/report-shop', label: 'Inventory Analytics' },
  { path: '/dashboard/user-profile_appointment', label: 'My Appointments' },
  { label: "My Inquiries", path: "/dashboard/UserInquiries"},
  { label: "My Reviews", path: "/dashboard/UserReviews"},
 
];

const UserDashboard = () => {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className='space-y-5 bg-white p-8 md:h-screen flex flex-col justify-between'>
      <div>
        <div className='nav__logo'>
          <Link to="/">Alpha IT Solutions<span>.</span></Link>
          <p className='italic mt-4 text-gray-500'>User dashboard</p>
        </div>
        <hr className='mt-5 text-gray-300' />
        <ul className='space-y-5 pt-5'>
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink 
                className={({ isActive }) => isActive ? "text-blue-600 font-bold" : 'text-black'} 
                end
                to={item.path}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
      <div className='mb-3'>
        <hr className='mb-3 text-gray-300'/>
        <button
          onClick={handleLogout}
          className="text-white font-medium px-5 py-2 rounded-md shadow-md transition duration-300 transform hover:scale-105"
          style={{
            textAlign: "center",
            background: "linear-gradient(to right, #d12222, #0245ff)",
            border: "none",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Logout
        </button>
      </div>
    </div>
  );
};

export default UserDashboard;
