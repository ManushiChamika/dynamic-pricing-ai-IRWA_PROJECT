// src/App.jsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import { ToastContainer } from "react-toastify"; // ✅ Import ToastContainer
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Break from './components/Break';
import { ThemeProvider } from './components/CustomBuilds/ThemeContext'; 
import './App.css';
import "react-toastify/dist/ReactToastify.css";

function App() {
  return (
    <ThemeProvider> {/* Wrap the app with the ThemeProvider for dark mode */}
      <Navbar />
      <Break />
      <ToastContainer position="top-right" autoClose={3000} /> {/* Ensure this is imported */}
      <Outlet />  {/* This is where page content (e.g., Home) will render */}
      <Footer />
    </ThemeProvider>
  );
}

export default App;
