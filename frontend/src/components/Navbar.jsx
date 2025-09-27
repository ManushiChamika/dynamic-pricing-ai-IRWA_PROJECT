import React, { useState, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MdSearch, MdShoppingCart, MdAccountCircle } from 'react-icons/md';
import { FaSun, FaMoon } from 'react-icons/fa';  // Import Sun and Moon icons for theme toggle
import logo from '../assets/AlphaITSolutionsLogo.jpg';
import { AuthContext } from '../context/authContext';
import { useTheme } from './CustomBuilds/ThemeContext';  // Import the useTheme hook
import { useDispatch } from 'react-redux';
import { persistor } from '../redux/store';

const adminDropDownMenus = [
  { label: "Dashboard", path: "/dashboard/admin" },
  { label: "AdminProfile", path: "/dashboard/AdminProfile" },
  { label: "Manage Items", path: "/dashboard/manage-products" },
  { label: "Add Product", path: "/dashboard/add-new-product" },
  { label: "Manage filters", path: "/dashboard/manage-filters" },
  { label: "Manage appointments", path: "/dashboard/manage-appointments" },
  { label: "Manage Pre-Builds", path: "/dashboard/prebuild-dashboard" },
  { label: "Setup Pre-Builds", path: "/dashboard/create-custom-prebuild" },
  { label: "Manage Inquiry", path: "/dashboard/InquiryManage"},
  { label: "Manage Review", path: "/dashboard/ReviewManage"},
  { label: "FAQ Manage", path: "/dashboard/FAQManage"},
  { label: "Blog Manage", path: "/dashboard/BlogManage"},
];

const userDropDownMenus = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Profile", path: "/dashboard/profile" },
  { label: "My Inquiries", path: "/dashboard/UserInquiries"},
  { label: "My Reviews", path: "/dashboard/UserReviews"},
  { path: '/dashboard/user-profile_appointment', label: 'My Appointments' },
];

const Navbar = () => {
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isDropDownOpen, setIsDropDownOpen] = useState(false);
  const navigate = useNavigate(); 
  
  const dispatch = useDispatch();

  // Access user and logout from AuthContext
  const { user, logout } = useContext(AuthContext);

  // Access the theme context
  const { isDark, toggleTheme } = useTheme();  // Retrieve the theme state and toggle function

  // Set dropdown menus based on the logged-in user's role
  const dropDownMenus =
    user && user.role === 'admin' ? adminDropDownMenus : user ? userDropDownMenus : [];

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > lastScrollY) {
        setIsVisible(false);
      } else {
        setIsVisible(true);
      }
      setLastScrollY(window.scrollY);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const handleDropDownToggle = () => {
    setIsDropDownOpen((prev) => !prev);
  };

  const handleLogout = () => {
    dispatch({ type: 'CLEAR_CART' });
    persistor.purge();
  
    if (logout) {
      logout();
    } else {
      console.log('Logging out...');
    }
  
    setIsDropDownOpen(false);
    navigate('/login');
    window.location.reload(); 
  };
  
  

  return (
    <header
      className={`pb-auto h-33 w-full bg-gray-100 border-black transition-transform duration-500 z-50 shadow-lg ${
        isVisible ? 'fixed top-0 left-0 translate-y-0' : 'fixed top-0 left-0 -translate-y-full'
      }`}
    >
      <nav className='max-w-screen-xl mx-auto px-5 flex justify-between items-center py-2'>
  {/* Logo */}
  <div className='pr-6 pl-4 w-32'> {/* Reduced padding & fixed width */}
    <img 
      src={logo} 
      alt="Alpha IT Solutions" 
      className="w-full h-auto"  // Make logo responsive within container
    />
  </div>

  {/* Brand Name - Reduced padding */}
  <div className='nav__logo pr-8 pt-6'>  {/* Changed from pr-80 to pr-8 */}
    <Link to="/" className="text-xl font-semibold whitespace-nowrap">
      <span>A</span>LPHA <span>I</span>T <span>S</span>OLUTIONS
    </Link>
  </div>
  
  {/* Navigation Links - Added whitespace-nowrap */}
  <ul className='nav__links flex gap-4 flex-1 justify-center ml-10'>  {/* Reduced gap to 4 */}
    <li className='link whitespace-nowrap'><Link to="/about">About</Link></li>
    <li className='link whitespace-nowrap'><Link to="/appointment">Services</Link></li>
    {/*<li className='link whitespace-nowrap'><Link to="/custom-prebuilds">Custom <br />Pre-<br />Builds</Link></li>*/}
    <li className='link whitespace-nowrap'><Link to="/custom-prebuilds">Custom Pre-Builds</Link></li>
    <li className='link'><Link to="/faq">FAQ</Link></li>
    <li className='link whitespace-nowrap'><Link to="/ContactUs">Contact</Link></li>
  </ul>

  <div className='nav__icons flex items-center gap-4 relative ml-35'>
          {/* Search Icon */}
          <Link to="/search">
            <MdSearch size={24} />
          </Link>
          
          {/* Cart Icon */}
          <Link to="/shoppingCart" className="relative">
            <MdShoppingCart size={24} />
            <sup className='absolute -top-2 -right-2 text-xs inline-block px-1.5 text-white rounded-full bg-primary'>
              {/* Optionally show the number of products */}
            </sup>
          </Link>
          
          {/* User Dropdown */}
          {user ? (
            <span className="relative">
              <MdAccountCircle
                size={24}
                onClick={handleDropDownToggle}
                className="cursor-pointer"
              />
              {isDropDownOpen && (
                <div className='absolute right-0 mt-3 p-4 w-65 bg-sky-100 border border-gray-200 rounded-lg shadow-lg z-50'>
                  <ul className='font-medium space-y-4 p-2'>
                    {dropDownMenus.map((menu, index) => (
                      <li key={index}>
                        <Link 
                          onClick={() => setIsDropDownOpen(false)}
                          className='dropdown-items'
                          to={menu.path}
                        >
                          {menu.label}
                        </Link>
                      </li>
                    ))}
                    <li>
                      <button 
                        onClick={handleLogout} 
                        
                        className="w-full text-left px-4 py-2 rounded-lg text-white font-semibold transition-all duration-300 shadow-md"
                        style={{
                          textAlign: "center",
                          background: "linear-gradient(to right, #d12222, #0245ff)",
                          border: "none",
                          cursor: "pointer",
                        }}
                        onMouseOver={(e) => e.target.style.transform = "scale(1.05)"}
                        onMouseOut={(e) => e.target.style.transform = "scale(1)"}
                      >
                        Logout
                      </button>
                    </li>
                  </ul>
                </div>
              )}
            </span>
          ) : (
            <Link to="/login">
              <MdAccountCircle size={24} />
            </Link>
          )}

          {/* Theme Toggle Button */}
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            style={{ position: "absolute", left: "170px" }} // Positioned at the top right
          >
            {isDark ? <FaMoon size={22} /> : <FaSun size={24} />} {/* Toggle between Sun and Moon icons */}
          </button>
        </div>
      </nav>
    </header>
  );
};

export default Navbar;