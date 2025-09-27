import axios from "axios";

export const getChatResponse = async (req, res) => {
  try {
    console.log('Received message:', req.body.message); // Debug log
    
    const response = await axios.post('http://127.0.0.1:5001/chat', {
      message: req.body.message
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('Full error:', {
      requestData: req.body,  // Log the complete incoming request
      errorDetails: error.response?.data || error.message
    });
    res.status(500).json({ 
      error: 'Failed to get response from chatbot',
      details: error.response?.data || error.message 
    });
  }
};