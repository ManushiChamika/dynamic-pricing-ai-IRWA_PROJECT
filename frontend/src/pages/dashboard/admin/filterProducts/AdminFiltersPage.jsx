// AdminFiltersPage.js
import React from "react";
import FilterForm from "./FilterForm";
import FiltersList from "./FiltersList";

const AdminFiltersPage = () => {
  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-100 mb-8">
          Filter Management Dashboard
        </h1>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form Section */}
          <div className="bg-gray-800 p-8 rounded-lg shadow-2xl">
            <FilterForm />
          </div>
          {/* Filter List Section */}
          <div className="bg-gray-800 p-8 rounded-lg shadow-2xl overflow-y-auto max-h-[80vh]">
            <FiltersList />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminFiltersPage;
