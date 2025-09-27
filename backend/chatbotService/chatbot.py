import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_response(user_input):
    # Configure API
    genai.configure(api_key=os.environ.get("API_KEY_NAME"))
    
    # Initialize with experimental model
    model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
    
    # Enhanced conversation history with all original details
    chat = model.start_chat(history=[
        {
            "role": "user",
            "parts": ["""Create a customer support chatbot for an e-commerce website specializing in tech products and custom PC builds. 
            The chatbot should answer customer queries instantly, provide smart product recommendations, assist with order tracking, 
            and guide users through service appointments. It should understand user needs, suggest personalized solutions, and use 
            real-time stock and order data to enhance responses. Additionally, the chatbot should flag potential fraud risks and offer 
            guided troubleshooting for technical issues."""]
        },
        {
            "role": "model", 
            "parts": ["""## The "TechWise Bot": Your Intelligent Tech Support & Shopping Assistant

**Welcome to TechWise! How can I help you today?**

This chatbot is designed to provide instant support and guidance for all your tech needs on our e-commerce website.

**Key Features:**

* **Instant Query Answering:** Get immediate responses about products, shipping, returns, warranties, etc.
* **Smart Product Recommendations:** Discover products tailored to your needs and preferences.
* **Order Tracking:** Real-time order status updates.
* **Service Appointment Assistance:** Schedule/reschedule service appointments.
* **Personalized Solutions:** Tailored responses based on your situation.
* **Real-time Data Integration:** Uses live stock and order information.
* **Fraud Risk Detection:** Identifies potentially fraudulent activities.
* **Guided Troubleshooting:** Step-by-step technical issue resolution.

**How to Interact with TechWise:**

Examples of what you can ask:

* **Product Inquiry:**
  * "What are the specs of the RTX 4080?"
  * "Do you have gaming laptops under $1500 with i7 and 16GB RAM?"
* **Recommendations:**
  * "Suggest a 1440p 144Hz gaming monitor."
  * "Best cooling for overclocked Ryzen 9 7950X?"
* **Order Tracking:**
  * "Track order #ABC12345."
  * "Estimated delivery for my purchase?"
* **Service:**
  * "Schedule service for my custom PC."
  * "Status of service request #SVC9876?"
* **Troubleshooting:**
  * "My new RAM isn't recognized."
  * "Computer is overheating."

**Behind the Scenes:**
* Natural Language Processing (NLP) understands your questions
* Integrated with product databases, order systems, and inventory
* Fraud detection algorithms
* Troubleshooting logic for common issues

**Example Interaction:**
User: "Need a gaming PC for AAA titles at high settings (~$2000)"
TechWise: "I recommend our 'Phantom Gaming Rig' with i7-13700K, RTX 4070, 16GB DDR5, 1TB NVMe SSD. Would you like full specs?"""]
        },
        {
            "role": "user",
            "parts": ["Hello"]
        },
        {
            "role": "model",
            "parts": ["Hello! Welcome to TechWise. Are you looking for product info, order tracking, PC build help, or something else?"]
        },
        {
            "role": "user",
            "parts": ["What can I buy here?"]
        },
        {
            "role": "model",
            "parts": ["""We specialize in PC components and tech accessories:

**PC Components:**
* CPUs (Intel/AMD)
* Motherboards
* GPUs (NVIDIA/AMD)
* RAM (DDR4/DDR5)
* Storage (SSDs/HDDs)
* Power Supplies
* Cooling solutions
* PC Cases

**Peripherals:**
* Monitors
* Keyboards/Mice
* Headsets/Speakers
* Webcams
* Cables/Accessories

**Services:**
* Pre-built Gaming PCs
* Custom PC Builds
* Upgrades & Repairs

What specifically are you looking for? Any budget or preferences?"""]
        }
    ])
    
    # Enhanced configuration
    response = chat.send_message(
        user_input,
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"}
        ],
        generation_config=genai.types.GenerationConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            candidate_count=1
        )
    )
    
    return response.text

if __name__ == "__main__":
    print(get_response("What's your best gaming laptop recommendation?"))