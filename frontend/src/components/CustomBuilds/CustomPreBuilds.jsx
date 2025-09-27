import React, { useState } from "react";
import CustomPreBuildList from "./CustomPreBuildList";

const CustomPreBuilds = () => {
  const [selectedBuilds, setSelectedBuilds] = useState([]); // For comparison feature

  return (
    <div className="min-h-screen flex flex-col items-center p-8 bg-gradient-to-t from-gray-900 via-blue-900 to-white dark:from-black dark:via-gray-800 dark:to-gray-900">
      <h1 className="text-4xl sm:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 mb-4 text-center">
        Explore Our Exclusive Collection of Custom Pre-Builds
      </h1>
      <div className="w-200 h-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 mx-auto mb-6"></div>
      <p className="text-gray-700 dark:text-gray-300 text-center text-xl max-w-4xl">
        Browse our exclusive collection of pre-configured PCs! Build the ultimate machine with high-quality components tailored to your needs.
      </p>

      {/* Custom Pre-Builds List */}
      <CustomPreBuildList selectedBuilds={selectedBuilds} setSelectedBuilds={setSelectedBuilds} />
      
    </div>
  );
};

export default CustomPreBuilds;