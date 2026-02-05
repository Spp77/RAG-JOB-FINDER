# RAG-JOB-FINDER 🚀

A modern, high-performance **Retrieval-Augmented Generation (RAG)** application designed for semantic job matching, career advice, and document management. This project features robust Role-Based Access Control (RBAC) and a built-in **Model Context Protocol (MCP)** server.

## ✨ Features

- **Advanced RAG Engine**: Uses LangChain and ChromaDB with Maximum Marginal Relevance (MMR) for diverse and high-quality job matches.
- **MCP Integration**: Includes a standalone MCP server (stdio transport) for searching and adding job descriptions via external tools (like Claude Desktop).
- **Role-Based Access Control (RBAC)**:
  - **Admins**: Full CRUD operations (Create, Read, Update, Delete) on job documents and resumes.
  - **Users**: Search functionality and history tracking (Read-only access to indexed data).
- **Modern UI**: Clean, glassmorphic design with real-time feedback.
- **Authentication**: Multiple auth layers including Django Auth and Clerk (Middleware ready).

## 🛠️ Technology Stack

- **Backend**: Django, Django REST Framework
- **AI/LLM**: LangChain, Hugging Face Inference API (Mistral-7B-Instruct)
- **Vector DB**: ChromaDB
- **Frontend**: Vanilla CSS (Global Design System), JavaScript
- **Protocol**: Model Context Protocol (MCP)

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Hugging Face API Token (Hugging Face Hub)

### 2. Installation
```powershell
# Clone the repository
git clone <your-repo-url>
cd RAG-JOB-FINDER-main

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
HUGGING_FACE_HUB_TOKEN=your_hf_token_here
CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
```

### 4. Database Setup
```powershell
python manage.py migrate
python manage.py createsuperuser  # Critical for Admin CRUD access
python manage.py runserver
```

### 5. Running the MCP Server
To use the MCP server with tools like Claude Desktop:
```powershell
python rag_search/mcp_server.py
```

## 🔐 RBAC Guide

| Role | Search Jobs | View History | Upload Documents | Delete Documents |
| :--- | :---: | :---: | :---: | :---: |
| **Guest** | ❌ | ❌ | ❌ | ❌ |
| **User** | ✅ | ✅ | ❌ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ |

## 📁 Project Structure

- `rag_search/`: Core application logic.
  - `services/rag_service.py`: Vector DB and LLM orchestration.
  - `mcp_server.py`: Standalone MCP implementation.
  - `middleware.py`: Custom auth and security.
- `vector_db/`: Persistent storage for document embeddings.
- `static/`: Modern styles and frontend logic.
- `templates/`: Django HTML templates.

## 🤝 Contributing
1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---
Built with ❤️ by Antigravity AI
