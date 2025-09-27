import React, { useEffect, useState } from "react";
import axios from "axios";

function UserManage() {
    const [users, setUsers] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get("http://localhost:5000/api/profile/get-all-users")
            .then((response) => {
                console.log("Fetched users:", response.data);
                setUsers(response.data);
                setLoading(false);
            })
            .catch((error) => {
                console.error("Error fetching users:", error);
                setError("Failed to load users. Please try again.");
                setLoading(false);
            });
    }, []);

    return (
        <div className="container mx-auto p-6">
            <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600 drop-shadow-lg mb-6 border-b-4 border-blue-500 inline-block">
                🚀 User Management
            </h2>
            {loading && <p className="text-center text-gray-600">Loading users...</p>}
            {error && <p className="text-center text-red-500">{error}</p>}

            <div className="overflow-x-auto bg-white shadow-lg rounded-lg p-4">
                <table className="w-full border-collapse">
                    <thead>
                        <tr className="bg-gray-800 text-white">
                            <th className="py-3 px-4 text-left">Name</th>
                            <th className="py-3 px-4 text-left">Email</th>
                            <th className="py-3 px-4 text-left">Address</th>
                            <th className="py-3 px-4 text-left">Contact Number</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.length > 0 ? (
                            users.map((user) => (
                                <tr key={user._id} className="border-b hover:bg-gray-100 transition duration-200">
                                    <td className="py-3 px-4">{user.name}</td>
                                    <td className="py-3 px-4">{user.email}</td>
                                    <td className="py-3 px-4">{user.address || "N/A"}</td>
                                    <td className="py-3 px-4">{user.contactNumber || "N/A"}</td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="4" className="py-3 px-4 text-center text-gray-500">
                                    No customers found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default UserManage;
