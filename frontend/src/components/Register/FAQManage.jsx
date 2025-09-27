import React, { useState, useEffect } from "react";
import axios from "axios";

const FAQManage = () => {
    const [faqs, setFaqs] = useState([]);
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [selectedFaq, setSelectedFaq] = useState(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showUpdateModal, setShowUpdateModal] = useState(false);

    useEffect(() => {
        fetchFAQs();
    }, []);

    // Fetch FAQs
    const fetchFAQs = async () => {
        try {
            const response = await axios.get("http://localhost:5000/api/faq/get-faqs");
            setFaqs(response.data);
        } catch (error) {
            console.error("Error fetching FAQs:", error);
        }
    };

    // Handle Add FAQ
    const handleAddFaq = async (e) => {
        e.preventDefault();
        try {
            await axios.post("http://localhost:5000/api/faq/add-faqs", { question, answer });
            resetForm();
            fetchFAQs();
        } catch (error) {
            console.error("Error adding FAQ:", error);
        }
    };

    // Handle Update FAQ
    const handleUpdateFaq = async (e) => {
        e.preventDefault();
        try {
            await axios.put(`http://localhost:5000/api/faq/update-faq/${selectedFaq._id}`, { question, answer });
            resetForm();
            fetchFAQs();
        } catch (error) {
            console.error("Error updating FAQ:", error);
        }
    };

    // Handle Delete FAQ
    const handleDeleteFaq = async (id) => {
        try {
            await axios.delete(`http://localhost:5000/api/faq/delete-faq/${id}`);
            fetchFAQs();
        } catch (error) {
            console.error("Error deleting FAQ:", error);
        }
    };

    // Handle Update Click
    const openUpdateModal = (faq) => {
        setSelectedFaq(faq);
        setQuestion(faq.question);
        setAnswer(faq.answer);
        setShowUpdateModal(true);
    };

    // Reset form & close modals
    const resetForm = () => {
        setSelectedFaq(null);
        setQuestion("");
        setAnswer("");
        setShowAddModal(false);
        setShowUpdateModal(false);
    };

    return (
    <div className="max-w-full mx-auto p-8 bg-white rounded-xl shadow-lg border border-gray-200">
  <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center relative">
    <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
      🛠️ FAQ Management
    </span>
  </h3>

  {/* Add FAQ Button */}
  <div className="flex justify-end mb-4">
    <button
      onClick={() => setShowAddModal(true)}
      className="bg-blue-600 text-white px-5 py-2 rounded-lg shadow-md hover:bg-blue-700 transition"
    >
      Add FAQ
    </button>
  </div>

  {/* FAQ Table */}
  <div className="overflow-x-auto">
    <table className="min-w-full bg-white border border-gray-300 shadow-md rounded-lg overflow-hidden">
      <thead>
        <tr className="bg-gray-800 text-white text-left">
          <th className="p-4 border">Question</th>
          <th className="p-4 border">Answer</th>
          <th className="p-4 border text-center">Actions</th>
        </tr>
      </thead>
      <tbody>
        {faqs.length === 0 ? (
          <tr>
            <td colSpan="3" className="p-4 text-center text-gray-500">No FAQs available.</td>
          </tr>
        ) : (
          faqs.map((faq) => (
            <tr key={faq._id} className="text-left border-t transition-all hover:bg-gray-100">
              <td className="p-4 border">{faq.question}</td>
              <td className="p-4 border">{faq.answer}</td>
              <td className="p-4 border flex justify-center gap-2">
                <button
                  onClick={() => openUpdateModal(faq)}
                  className="bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-md hover:bg-yellow-600 transition"
                >
                  Update
                </button>
                <button
                  onClick={() => handleDeleteFaq(faq._id)}
                  className="bg-red-500 text-white px-4 py-2 rounded-lg shadow-md hover:bg-red-600 transition"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  </div>

  {/* Add & Update FAQ Modal */}
  {(showAddModal || showUpdateModal) && (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
        <h3 className="text-xl font-semibold mb-4 text-center">
          {showAddModal ? "Add FAQ" : "Update FAQ"}
        </h3>
        <form onSubmit={showAddModal ? handleAddFaq : handleUpdateFaq}>
          <div className="mb-4">
            <label className="block text-gray-700 font-medium">Question</label>
            <input
              type="text"
              placeholder="Enter question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 font-medium">Answer</label>
            <textarea
              placeholder="Enter answer"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              required
              className="w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div className="flex justify-end gap-3">
            <button
              type="submit"
              className={`px-5 py-2 rounded-lg shadow-md text-white ${
                showAddModal ? "bg-green-500 hover:bg-green-600" : "bg-yellow-500 hover:bg-yellow-600"
              } transition`}
            >
              {showAddModal ? "Add FAQ" : "Update FAQ"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="bg-gray-500 text-white px-5 py-2 rounded-lg shadow-md hover:bg-gray-600 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )}
</div>

    );
};

export default FAQManage;