import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { AuthContext } from "../../context/authContext";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import { FaUserEdit, FaKey, FaTrash } from "react-icons/fa";

function AdminProfile() {
    const { user, setUser } = useContext(AuthContext);
    const [profile, setProfile] = useState({
      name: user?.name || "",
      email: user?.email || "",
    });
    const [newPassword, setNewPassword] = useState("");
    const [oldPassword, setOldPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [showEditForm, setShowEditForm] = useState(false);
    const [showPasswordForm, setShowPasswordForm] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    
    const Navigate = useNavigate();

    const handleChange = (e) => {
        setProfile({ ...profile, [e.target.name]: e.target.value });
    };

    const handleUpdateProfile = async (e) => {
      e.preventDefault();
      setLoading(true);
      try {
          const token = localStorage.getItem("token");
          const { data } = await axios.put(
              "http://localhost:5000/api/profile/update",
              profile, 
              { headers: { Authorization: `Bearer ${token}` } }
          );

          setUser(data.updatedUser); // Update global state
          toast.success("Profile updated successfully!");
          setShowEditForm(false);
      } catch (error) {
          toast.error(error.response?.data?.message || "Profile update failed.");
      }
      setLoading(false);
    };

    const handleChangePassword = async () => {
        if (!oldPassword || !newPassword) {
            toast.error("Please enter both old and new passwords.");
            return;
        }
        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            await axios.put(
                "http://localhost:5000/api/profile/change-password",
                { oldPassword, newPassword },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            toast.success("Password changed successfully!");
            setOldPassword("");
            setNewPassword("");
            setShowPasswordForm(false);
        } catch (error) {
            toast.error(error.response?.data?.message || "Password change failed.");
        }
        setLoading(false);
    };

    const handleDeleteAccount = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            await axios.delete("http://localhost:5000/api/profile/delete", {
                headers: { Authorization: `Bearer ${token}` }
            });

            toast.success("Account deleted successfully!");
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            Navigate('/');
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to delete account.");
        }
        setLoading(false);
    };
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-700 flex flex-col items-center p-6 text-white">
      <h2 className="text-5xl font-bold text-white-900 text-center my-20 border-b-4 border-blue-600 pb-2">Admin Profile</h2>
      <div className="max-w-4xl w-full bg-gray-800 shadow-lg rounded-xl p-8 border border-gray-600">
        <h2 className="text-2xl font-semibold text-center mb-4">Welcome, {profile.name}!</h2>
        
        {!showEditForm && !showPasswordForm && (
          <>
            <div className="mb-6 p-6 bg-gray-700 rounded-lg shadow-sm text-center">
              <p className="text-lg"><strong>Name:</strong> {profile.name}</p>
              <p className="text-lg"><strong>Email:</strong> {profile.email}</p>
            </div>

            <div className="flex flex-col space-y-4">
              <button onClick={() => setShowEditForm(true)} className="flex items-center justify-center w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold">
                <FaUserEdit className="mr-2" /> Edit Profile
              </button>
              <button onClick={() => setShowPasswordForm(true)} className="flex items-center justify-center w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-semibold">
                <FaKey className="mr-2" /> Change Password
              </button>
              <button onClick={() => setShowDeleteModal(true)} className="flex items-center justify-center w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 transition font-semibold">
                <FaTrash className="mr-2" /> Delete Account
              </button>
            </div>
          </>
        )}

        {showEditForm && (
          <div className="mt-6 p-6 bg-gray-700 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-4">Edit Profile</h3>
            <label className="block mb-2">Name:</label>
            <input type="text" name="name" value={profile.name} onChange={handleChange} className="w-full px-4 py-2 border rounded-lg text-black" />
            <label className="block mb-2 mt-2">Email Address:</label>
            <input type="email" name="email" value={profile.email} onChange={handleChange} className="w-full px-4 py-2 border rounded-lg text-black" />
            <button onClick={handleUpdateProfile} disabled={loading} className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold mt-4">
              {loading ? "Updating..." : "Save Changes"}
            </button>
            <button onClick={() => setShowEditForm(false)} className="w-full bg-gray-500 text-white py-3 rounded-lg hover:bg-gray-600 transition font-semibold mt-2">
              Cancel
            </button>
          </div>
        )}

        {showPasswordForm && (
          <div className="mt-6 p-6 bg-gray-700 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-4">Change Password</h3>
            <label className="block mb-2">Old Password:</label>
            <input type="password" placeholder="Enter old password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} className="w-full px-4 py-2 border rounded-lg text-black" />
            <label className="block mb-2 mt-2">New Password:</label>
            <input type="password" placeholder="Enter new password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full px-4 py-2 border rounded-lg text-black" />
            <button onClick={handleChangePassword} disabled={loading} className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-semibold mt-4">
              {loading ? "Changing..." : "Save Password"}
            </button>
            <button onClick={() => setShowPasswordForm(false)} className="w-full bg-gray-500 text-white py-3 rounded-lg hover:bg-gray-600 transition font-semibold mt-2">
              Cancel
            </button>
          </div>
        )}

        {showDeleteModal && (
          <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-600 text-center">
              <p className="text-xl font-bold mb-4">Are you sure you want to delete your account?</p>
              <div className="flex justify-center space-x-4">
                <button onClick={handleDeleteAccount} className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 font-semibold">
                  Yes, Delete
                </button>
                <button onClick={() => setShowDeleteModal(false)} className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 font-semibold">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>

)};

export default AdminProfile
