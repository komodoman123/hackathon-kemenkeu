SiRUPA - Generative AI Chatbot untuk Transparansi dan Akses Data Pengadaan Pemerintah SiRUP Assistant

Project Structure

.
├── backend
│   └── openai           # Backend folder containing the Flask application 
├── chatbot              # Frontend folder
└── README.md            # Project README file

Features
Backend: A Flask-based API located in /backend/openai that interfaces with OpenAI to handle chatbot queries.
Frontend: A React application in the /chatbot folder, set up with Vite for fast development.

Getting Started
Prerequisites
Node.js: Required to run the frontend with Vite.
Python: Required to run the Flask backend.

Installation
Clone the Repository:

git clone https://github.com/yourusername/hackathon-kemenkeu.git

Navigate to the backend directory and install dependencies:

cd backend/openai
pip install -r requirements.txt
python main.py

Frontend Setup
Navigate to the chatbot directory and install dependencies:

cd ../chatbot
npm install
Start the Vite development server:

npm run dev


Usage
Frontend: Access the chatbot interface at http://localhost:5173.
Backend: The API endpoint will be at http://localhost:5000.
