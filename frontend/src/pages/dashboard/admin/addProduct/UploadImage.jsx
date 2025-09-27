import React, { useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { getBaseURL } from "../../../../utils/baseUtil";

const UploadImage = ({ name, setImage }) => {
    const [loading, setLoading] = useState(false);
    const [url, setUrl] = useState("");

    // Upload file to backend
    const uploadSingleImage = async (file) => {
        try {
            setLoading(true);

            // Create FormData object
            const formData = new FormData();
            formData.append("image", file);

            // Send to backend
            const res = await axios.post(`${getBaseURL()}/api/uploadImage`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
              });
              

            console.log("Upload Response:", res.data);

            if (res.data && res.data.imageUrl) {
                const imageUrl = `${getBaseURL()}${res.data.imageUrl}`;
                setUrl(imageUrl);
                setImage(imageUrl);
                toast.success("Image uploaded successfully!");
            } else {
                toast.error("Image upload failed, please try again.");
            }
        } catch (error) {
            console.error("Upload Error:", error.response ? error.response.data : error.message);
            toast.error("Error uploading image");
        } finally {
            setLoading(false);
        }
    };

    // Handle file selection
    const uploadImage = async (event) => {
        const file = event.target.files[0]; // Get the first selected file
        if (!file) return;
        await uploadSingleImage(file);
    };

    return (
        <div>
            <label htmlFor={name} className="block text-sm font-medium text-gray-700">
                Upload Image
            </label>
            <input 
                type="file"
                name={name}
                id={name}
                accept="image/*"
                onChange={uploadImage}
                className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 text-sm text-gray-800 shadow-sm focus:ring-2 focus:ring-blue-500 transition"
            />
            {loading && <div className="mt-2 text-sm text-blue-600">Uploading image...</div>}
            {url && (
                <div className="mt-2 text-sm text-green-600">
                    <p>Image uploaded successfully!</p>
                    <img src={url} alt="Uploaded" className="w-32 h-32 object-cover mt-2 rounded-lg shadow" />
                </div>
            )}
        </div>
    );
};

export default UploadImage;
