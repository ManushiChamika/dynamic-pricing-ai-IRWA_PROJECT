import React, { useState } from 'react';
import ProductCategoryAnalytics from './ProductCategoryAnalytics';
import FilterForm from '../filterProducts/FilterForm';
import FiltersList from '../filterProducts/FiltersList';
import AddProduct from '../addProduct/AddProduct';
import InventoryTable from './ManageInventory';
import ManageProducts from '../manageProducts/ManageProducts';

const AllInventoryRelated = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const pageHints = [
    { title: "Product Category Analytics", next: "Manage Filters" },
    { title: "Manage Filters, If filters are already available", next: "Add New Product" },
    { title: "Add New Product based on the filters", next: "Manage Products" },
    { title: "Manage Products under each category", next: "Manage Inventory" },
    { title: "Manage Inventory(Stock, discounts) of each product added", next: "Product Category Analytics" }
  ];
  
  const renderPageContent = () => {
    switch (currentPage) {
      case 1:
        return (
          <div>
            <h1 style={{ fontSize: '2rem', color: '#0984e3', marginBottom: '1rem' }}>
              Product Category Analytics
            </h1>
            <ProductCategoryAnalytics />
           
          </div>
        );
      case 2:
        return (
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start', height: '90vh' }}>
           <div style={{ flex: 2, overflowY: 'auto', height: '100%', maxHeight: '90vh', paddingRight: '0rem' }}>
              <h1 style={{ fontSize: '2rem', color: '#0984e3', marginBottom: '1rem' }}>Filter Products</h1>
              <FilterForm />
            </div>
            <div style={{ flex: 2, overflowY: 'auto', height: '100%', maxHeight: '90vh', paddingRight: '0rem' }}>
              <h1 style={{ fontSize: '2rem', color: '#0984e3', marginBottom: '1rem' }}>Filters List</h1>
              <FiltersList />
            
            </div>
          </div>
        );
      case 3:
        return (
          <div>
            
            <AddProduct />

          </div>
        );
      case 4:
        return (
          <div className="max-h-[80vh] overflow-y-auto">
            
            <ManageProducts />

          </div>
        );
      case 5:
        return (
          <div className="max-h-[80vh] overflow-y-auto">
            <InventoryTable />
           
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div
  style={{
    textAlign: 'center',
    margin: '20px',
    background: 'linear-gradient(to bottom right, #6a89cc, #74b9ff)',
    borderRadius: '25px',
    boxShadow: '0px 6px 15px rgba(0, 0, 0, 0.2)',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
    color: '#2d3436',
  }}
>
  <div
    style={{
      padding: '20px',
      minHeight: '200px',
      background: '#f5f6fa',
      borderRadius: '20px',
      boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.1)',
      transition: 'transform 0.2s ease-in-out',
    }}
  >
    {/* Helper Box First */}
    <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#dfe6e9', borderRadius: '10px' }}>
      <h3 style={{ marginBottom: '10px', color: '#2d3436' }}>
        You're currently viewing: <strong>{pageHints[currentPage - 1].title}</strong>
      </h3>
      <button
        onClick={() => setCurrentPage(currentPage < 5 ? currentPage + 1 : 1)}
        style={{
          backgroundColor: '#00cec9',
          color: 'white',
          padding: '8px 20px',
          borderRadius: '20px',
          cursor: 'pointer',
          fontWeight: 'bold',
          transition: 'background-color 0.2s',
        }}
        onMouseEnter={(e) => (e.target.style.backgroundColor = '#0984e3')}
        onMouseLeave={(e) => (e.target.style.backgroundColor = '#00cec9')}
      >
        Go to {pageHints[currentPage - 1].next}
      </button>
    </div>

    {/* Page Content Below */}
    {renderPageContent()}
  </div>
      <div style={{ marginTop: '20px' }}>
        <button
          onClick={() => setCurrentPage(currentPage > 1 ? currentPage - 1 : 5)}
          style={{
            padding: '10px 20px',
            borderRadius: '30px',
            backgroundColor: '#0984e3',
            color: 'white',
            margin: '0 10px',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease-in-out',
          }}
          onMouseEnter={(e) => (e.target.style.backgroundColor = '#6c5ce7')}
          onMouseLeave={(e) => (e.target.style.backgroundColor = '#0984e3')}
        >
          Previous
        </button>
        <span style={{ color: '#0984e3', fontWeight: 'bold', fontSize: '18px' }}>
          Page {currentPage}
        </span>
        <button
          onClick={() => setCurrentPage(currentPage < 5 ? currentPage + 1 : 1)}
          style={{
            padding: '10px 20px',
            borderRadius: '30px',
            backgroundColor: '#0984e3',
            color: 'white',
            margin: '0 10px',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease-in-out',
          }}
          onMouseEnter={(e) => (e.target.style.backgroundColor = '#6c5ce7')}
          onMouseLeave={(e) => (e.target.style.backgroundColor = '#0984e3')}
        >
          Next
        </button>
      </div>
      <div style={{ marginTop: '10px' }}>
        {[1, 2, 3, 4, 5].map((page) => (
          <button
            key={page}
            onClick={() => setCurrentPage(page)}
            style={{
              margin: '0 5px',
              backgroundColor: page === currentPage ? '#6a89cc' : '#74b9ff',
              color: 'white',
              borderRadius: '30px',
              padding: '10px',
              cursor: 'pointer',
              boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.1)',
              transition: 'transform 0.2s ease-in-out',
            }}
            onMouseEnter={(e) => (e.target.style.transform = 'scale(1.1)')}
            onMouseLeave={(e) => (e.target.style.transform = 'scale(1)')}
          >
            {page}
          </button>
        ))}
      </div>
    </div>
  );
};

export default AllInventoryRelated;