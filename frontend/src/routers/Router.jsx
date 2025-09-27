import React from 'react';
import { createBrowserRouter } from 'react-router-dom';
import App from '../App';
import Home from '../pages/Home';
import CustomPreBuilds from '../components/CustomBuilds/CustomPreBuilds';
import AppointmentDashboard from '../components/Appointment/Appointment_Dashboard';
import AppointmentForm from '../components/Appointment/Appointment_form';
import AppointmenentAI from "../components/Appointment/AppointmentAi";
import DraftedTechniciansReports from '../components/Appointment/DraftedTechniciansReports';
import Login from '../components/Register/Login';
import Register from '../components/Register/Register';
import ForgotPassword from '../components/Register/ForgotPassword';
import VerifyOTP from '../components/Register/VerifyOTP';
import FAQManage from '../components/Register/FAQManage';
import FAQ from '../components/Register/FAQ';
import ProductCategory from '../components/shop/ProductCategory';
import ProtectedRoute from "../routers/ProtectedRoute";  
import DashboardLayout from "../pages/dashboard/DashboardLayout";
import ContactUs from '../components/Contact/ContactUs';
import AdminPanel from '../pages/dashboard/admin/dashboard/AdminDMain' 
import AboutUs from '../components/Aboutus';

import AddProduct from '../pages/dashboard/admin/addProduct/AddProduct';
import ManageProducts from '../pages/dashboard/admin/manageProducts/ManageProducts';
import ManageInventory from '../pages/dashboard/admin/inventoryManagement/ManageInventory';
import ProductDetails from '../components/shop/ProductDetails';
import SearchPage from '../components/shop/search/SearchPage';
import ManageAppointments from "../pages/dashboard/appointment/manage-appointments";
import ManageOrder from "../pages/dashboard/admin/manageOrder/OrderList";
import CustomerOrder from "../pages/dashboard/admin/manageOrder/CustomerOrderList";
import SuccessOrder from '../pages/dashboard/admin/manageOrder/SuccessOrder';
import InvoicePage from "../pages/dashboard/Finance/InvoicePage";
import RevenuePage from "../pages/dashboard/Finance/RevenuePage";
import ManageTaxes from '../pages/dashboard/Finance/ManageTaxes';
import PettyCash from '../pages/dashboard/Finance/PettyCash';
import UserAppointment from "../pages/dashboard/appointment/user-profile_appointment"

import Profile from '../components/Register/Profile';
import UserManage from '../components/Register/UserManage';
import AdminProfile from '../components/Register/AdminProfile';

//Blog Components
import BlogManage from '../components/Blog/BlogManage';
import UserBlog from '../components/Blog/UserBlog';

//Inquiry Components
import InquiryForm from '../components/Inquiry/InquiryForm';
import InquiryManage from '../components/Inquiry/InquiryManage';
import UserInquiries from '../components/Inquiry/UserInquiries';
import InquiryChart from '../components/InquiryChart/InquiryChart';

//Review Components
import UserReviews from '../components/Reviews/UserReviews';
import ReviewManage from '../components/Reviews/ReviewManage';
import ReviewForm from '../components/Reviews/ReviewForm';
import ReviewChart from '../components/ReviewChart/ReviewChart';

// CustomBuilds Components
import GamingBuilds from '../components/CustomBuilds/GamingBuilds';
import BudgetBuilds from '../components/CustomBuilds/BudgetBuilds';
import GamingBuildDetail from '../components/CustomBuilds/GamingBuildDetail';
import BudgetBuildDetail from '../components/CustomBuilds/BudgetBuildDetail'; 
import CreateCustomBuild from '../components/CustomBuilds/CreateCustomPreBuild';
import PreBuildDashboard from "../components/CustomBuilds/PreBuildDashboard";
import EditCustomPreBuild from '../components/CustomBuilds/EditCustomPreBuild';



//order management
import ShoppingCart from '../pages/OrderManagement/ShoppingCart';
import CheckoutForm from '../components/OrderManagement/CheckoutForm';
import PickupForm from '../components/OrderManagement/pickupForm';
import CodForm from '../components/OrderManagement/CodForm';
import OrderSupportChat from '../components/OrderManagement/OrderSupportChat';
import CatalogReportInline from '../pages/dashboard/user/shop/report/CatalogReportInline ';
import OrderList from '../components/OrderManagement/OrderList';
import TransactionPage from '../pages/dashboard/Finance/TransactionPage';
import ImageUploader from '../components/shop/ai/ImageUploader';
import UserInventoryDashboard from '../components/shop/UserInventoryDashboard';

import BuildSuggestor from '../components/CustomBuilds/CustomBuildsAI/BuildSuggestor';
import AllInventoryRelated from '../pages/dashboard/admin/inventoryManagement/AllInventoryRelated';
import PreBuildAnalytics from '../components/CustomBuilds/PreBuildAnalytics';


const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { path: '', element: <Home /> },
      { path: 'products/:category', element: <ProductCategory /> },
      { path: 'about', element: <AboutUs/> },
      { path: 'appointment', element: <ProtectedRoute><AppointmentDashboard /></ProtectedRoute> },
      { path: 'AppointmenentAI', element: <ProtectedRoute><AppointmenentAI /></ProtectedRoute> },
      { path: 'draftedTechnicianReport', element: <ProtectedRoute><DraftedTechniciansReports /></ProtectedRoute> },
      { path: 'appointment-form', element: <ProtectedRoute><AppointmentForm /></ProtectedRoute> },
      

      { path: 'faq', element: <FAQ /> },
      { path: 'ReviewForm', element:<ReviewForm/>},
      { path: 'UserReviews', element:<UserReviews/>},
      { path: 'InquiryForm', element:<InquiryForm/>},
      { path: 'UserInquiries', element:<UserInquiries/>},
      { path: 'ContactUs', element:<ContactUs/>},
      { path: 'UserBlog', element:<UserBlog/>},

      // CustomBuilds routes
      { path: 'custom-prebuilds', element: <CustomPreBuilds /> },
      { path: 'shop/:productId', element: <ProductDetails /> },
      { path: 'search', element: <SearchPage /> },
      { path: 'gaming-builds', element: <GamingBuilds /> },
      { path: 'budget-builds', element: <BudgetBuilds /> },        
      { path: 'budget-builds/:id', element: <ProtectedRoute><BudgetBuildDetail /></ProtectedRoute> }, 
      { path: 'gaming-builds/:id', element: <ProtectedRoute><GamingBuildDetail /></ProtectedRoute> },

      
      //order routes
      { path: 'ShoppingCart', element: <ProtectedRoute><ShoppingCart /></ProtectedRoute> },
      { path: 'orderList', element: <ProtectedRoute><OrderList /></ProtectedRoute> },
      { path: 'CheckoutForm', element: <ProtectedRoute><CheckoutForm /></ProtectedRoute> },
      { path: 'CheckoutForm/:email', element: <ProtectedRoute><CheckoutForm /></ProtectedRoute> },
      { path: 'PickupForm', element: <ProtectedRoute><PickupForm /></ProtectedRoute> },
      { path: 'CodForm', element: <ProtectedRoute><CodForm /></ProtectedRoute> },
      { path: 'orderAI', element: <ProtectedRoute><orderAI /></ProtectedRoute> },
      { path: 'OrderSupportChat', element: <ProtectedRoute><OrderSupportChat /></ProtectedRoute> },

      { path: 'budget-builds/:id', element: <BudgetBuildDetail /> },  
      { path: 'edit-custom-pre-build/:id', element: <EditCustomPreBuild /> }, 
       // Updated route for your custom dashboard

      { path: 'edit-custom-pre-build/:id', element: <EditCustomPreBuild /> }, 
      { path: 'prebuild-dashboard', element: <ProtectedRoute><PreBuildDashboard /></ProtectedRoute>  }, 

      //ai product routes
      { path: 'AI-Engine', element: <ProtectedRoute allowedRoles={["user", "admin"]}><ImageUploader /></ProtectedRoute> },

      

      { path: 'edit-custom-pre-build/:id', element: <EditCustomPreBuild /> }, // ✅ New Route
      { path: 'prebuild-dashboard', element: <ProtectedRoute><PreBuildDashboard /></ProtectedRoute>  }, // Updated route for your custom dashboard  
      //Prebuilds analytics route
      { path: 'prebuild-analytics', element: <ProtectedRoute allowedRoles={["admin"]}><PreBuildAnalytics /></ProtectedRoute> },
      //AI Build Suggestor Route
      { path: 'AI-build-suggestor', element: <ProtectedRoute allowedRoles={["user", "admin"]}><BuildSuggestor /></ProtectedRoute> }, 
    ]
  },

  // Authentication routes
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  { path: '/forgot-password', element: <ForgotPassword /> },
  { path: '/verify-otp', element: <VerifyOTP /> },
  // Dashboard routes
  {
    path: "/dashboard",
    element: <ProtectedRoute><DashboardLayout /></ProtectedRoute>,
    children: [
      // Customer routes
      { path: '', element: <div>Dashboard Home</div> },
      { path: 'reviews', element: <div>Reviews</div> },
      { path: 'report-shop', element: <UserInventoryDashboard/> },
      {path: 'user-profile_appointment', element: <UserAppointment /> },
      { path: 'Profile', element: <div><Profile/></div> },
      { path: 'UserInquiries', element: <div><UserInquiries/></div> },
      { path: 'UserReviews', element:<div><UserReviews/></div>},

      // Admin routes
      { path: 'admin', element: <ProtectedRoute allowedRoles={["admin"]}><div><AdminPanel/></div></ProtectedRoute> },
      { path: 'add-new-product', element: <ProtectedRoute allowedRoles={["admin"]}><AllInventoryRelated /></ProtectedRoute> },
      { path: 'UserManage', element: <ProtectedRoute allowedRoles={["admin"]}><div><UserManage/></div></ProtectedRoute> },
      { path: 'manage-appointments', element: <ProtectedRoute allowedRoles={["admin"]}><ManageAppointments /></ProtectedRoute> },
      { path: 'create-custom-prebuild', element: <ProtectedRoute allowedRoles={["admin"]}><CreateCustomBuild /></ProtectedRoute> },
      { path: 'prebuild-dashboard', element: <ProtectedRoute allowedRoles={["admin"]}><PreBuildDashboard /></ProtectedRoute>  },
      { path: 'manageOrder', element: <ProtectedRoute allowedRoles={["admin"]}><ManageOrder /></ProtectedRoute>  },
      { path: 'customerOrder', element: <ProtectedRoute allowedRoles={["admin"]}><CustomerOrder /></ProtectedRoute>  },
      { path: 'SuccessOrder/:id', element: <ProtectedRoute allowedRoles={["admin"]}><SuccessOrder /></ProtectedRoute>  },
      { path: 'invoicePage', element: <ProtectedRoute allowedRoles={["admin"]}><InvoicePage /></ProtectedRoute>  },
      { path: 'TransactionPage', element: <ProtectedRoute allowedRoles={["admin"]}><TransactionPage /></ProtectedRoute>  },
      { path: 'InvoicePage', element: <ProtectedRoute allowedRoles={["admin"]}><InvoicePage /></ProtectedRoute>  },
      { path: 'RevenuePage', element: <ProtectedRoute allowedRoles={["admin"]}><RevenuePage /></ProtectedRoute>  },
      { path: 'ManageTaxes', element: <ProtectedRoute allowedRoles={["admin"]}><ManageTaxes /></ProtectedRoute>  },
      { path: 'PettyCash', element: <ProtectedRoute allowedRoles={["admin"]}><PettyCash /></ProtectedRoute>  },
      { path: 'prebuild-dashboard', element: <ProtectedRoute allowedRoles={["admin"]}><PreBuildDashboard /></ProtectedRoute>  },
      { path: 'ReviewManage', element: <ProtectedRoute allowedRoles={["admin"]}><div><ReviewManage/></div></ProtectedRoute> },
      { path: 'InquiryManage', element: <ProtectedRoute allowedRoles={["admin"]}><div><InquiryManage/></div></ProtectedRoute>},
      { path: 'FAQManage', element: <ProtectedRoute allowedRoles={["admin"]}><div><FAQManage/></div></ProtectedRoute>},
      { path: 'BlogManage', element: <ProtectedRoute allowedRoles={["admin"]}><div><BlogManage/></div></ProtectedRoute>},
      { path: 'AdminProfile', element: <ProtectedRoute allowedRoles={["admin"]}><div><AdminProfile/></div></ProtectedRoute>},
      { path: 'InquiryChart', element: <ProtectedRoute allowedRoles={["admin"]}><div><InquiryChart/></div></ProtectedRoute>},
      { path: 'ReviewChart', element: <ProtectedRoute allowedRoles={["admin"]}><div><ReviewChart/></div></ProtectedRoute>},

    ]
  }
]);

export default router;
