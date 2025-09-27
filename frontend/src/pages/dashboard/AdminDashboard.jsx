import React, { useContext, useState, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../context/authContext';
import '../../styles/admin_dashboard.css'; // Import the CSS file

const navItems = [
  { path: '/dashboard/admin', label: 'Dashboard' },
  { path: '/dashboard/AdminProfile', label: 'Profile' },
  { path: '/dashboard/add-new-product', label: 'Inventory Management' },
  { path: '/dashboard/UserManage', label: 'User Manage' },
  { path: '/dashboard/manage-appointments', label: 'Manage Appointments' },
  { path: '/dashboard/create-custom-prebuild', label: 'Create Custom Prebuild' },
  { path: '/dashboard/prebuild-dashboard', label: 'Manage Custom Prebuild' },
  { path: '/dashboard/manageOrder', label: 'Manage Order' },
  { path: '/dashboard/customerOrder', label: 'Manage Customer Orders' },
  { path: '/dashboard/TransactionPage', label: 'Manage Transaction' },
  { path: '/dashboard/InvoicePage', label: 'Manage Invoice' },
  { path: '/dashboard/RevenuePage', label: 'Show Revenue' },
  { path: '/dashboard/ManageTaxes', label: 'Manage Taxes' },
  { path: '/dashboard/PettyCash', label: 'Manage Petty Cash' },
  { path: '/dashboard/prebuild-dashboard', label: 'Manage Custom Prebuild' },
  { path: '/dashboard/InquiryManage', label: 'Inquiry Manage'},
  { path: '/dashboard/ReviewManage', label: 'Review Manage'},
  { path: '/dashboard/FAQManage', label: 'FAQ Manage'},
  { path: '/dashboard/BlogManage', label: 'Blog Manage'},
];

const AdminDashboard = () => {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();

  // Clock state and effect for updating time
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timerID = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => {
      clearInterval(timerID);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="admin-dashboard bg-sky-100 rounded-lg shadow-lg border border-sky-400 p-6 text-gray-800 flex flex-col h-screen sticky top-0">
      <div className="dashboard-header flex-1 overflow-y-auto">
        <div className="nav__logo mb-4">
          <Link to="/" className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-800 hover:from-indigo-600 hover:to-blue-700 transition-all duration-300">
            Alpha IT Solutions<span className="text-indigo-600">.</span>
          </Link>
          <hr className="border-t border-gray-200 my-2" />
          <p className="mt-4 text-gray-600 text-sm tracking-wider">
            <span className="text-sm inline-block px-2 py-1 bg-gray-100 rounded border-l-2 border-indigo-500 font-bold">ADMIN DASHBOARD</span>
          </p>
        </div>
        <hr className="border-t border-gray-200 my-4" />
        <ul className="nav-items flex flex-col gap-2">
          {navItems.map((item) => (
            <li key={item.path} className="relative">
              <NavLink
                className={({ isActive }) =>
                  isActive
                    ? "flex items-center px-4 py-2 rounded-md bg-gradient-to-r from-blue-400 to-red-200 text-sky-100 font-medium shadow-md transition-all duration-300"
                    : "flex items-center px-4 py-2 rounded-md bg-sky-50 hover:bg-red-200 text-gray-300 hover:text-indigo-700 font-medium hover:shadow-sm transform hover:translate-x-1 transition-all duration-300"
                }
                end
                to={item.path}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-auto">
        <hr className="border-t border-gray-200 my-4" />
        <div className="flex flex-col gap-4">
          <div className="clock-container bg-fuchsia-200 border border-sky-300 rounded-md p-3 text-center shadow-sm">
            <div className="text-indigo-700 font-mono text-xl tracking-wide">
              {/* Time and Date */}
              <div>{time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}</div>
              <div>{time.toLocaleDateString([], { year: 'numeric', month: '2-digit', day: '2-digit' })}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="logout-button w-full py-2 px-4 rounded-md bg-gradient-to-r from-gray-200 to-gray-300 hover:from-red-500 hover:to-red-600 text-gray-700 hover:text-white font-medium transition-all duration-300 shadow-sm flex items-center justify-center"
            aria-label="Logout"
          >
            <span>Logout</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;