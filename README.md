# DeepInsight

A comprehensive document ontology extraction and graph database export system. Upload documents, create AI-powered ontologies, extract structured data, and export to Neo4j or AWS Neptune.

## Features

- **Document Processing**: Support for PDF, DOCX, TXT, and Markdown files
- **AI-Powered Ontology Creation**: Automatic ontology generation using Claude Sonnet 4
- **Data Extraction**: Structured data extraction using custom ontologies
- **Graph Database Export**: Export to Neo4j and AWS Neptune formats
- **User Management**: Secure authentication with JWT tokens
- **Modern UI**: React with Material-UI design system

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Anthropic API key (Claude)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd deepinsight
```

### 2. Backend Setup

```bash
# Run the backend startup script
./start_backend.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create necessary directories
- Start the FastAPI server on http://localhost:8000

### 3. Frontend Setup

In a new terminal:

```bash
# Run the frontend startup script
./start_frontend.sh
```

This will:
- Install Node.js dependencies
- Create environment configuration
- Start the React dev server on http://localhost:3000

### 4. Configure API Keys

Edit `backend/.env` and add your Anthropic API key:

```env
ANTHROPIC_API_KEY=your-actual-anthropic-api-key-here
```

## API Documentation

Once the backend is running, visit:
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Usage

1. **Register/Login**: Create an account or sign in
2. **Upload Documents**: Drag & drop PDF, DOCX, TXT, or MD files
3. **Create Ontologies**: AI automatically generates ontologies from your documents
4. **Extract Data**: Run extraction to get structured graph data
5. **Export**: Download CSV files for Neo4j or AWS Neptune import

## Architecture

### Backend (FastAPI)
- **Authentication**: JWT-based user management
- **Document Processing**: Multi-format document parsing
- **AI Integration**: Claude Sonnet 4 for ontology creation and data extraction
- **Database**: SQLite for development, easily upgradeable to PostgreSQL
- **Export System**: CSV generation for graph databases

### Frontend (React)
- **UI Framework**: Material-UI with custom theming
- **State Management**: React Context for authentication
- **File Upload**: Drag & drop with progress tracking
- **Graph Visualization**: vis.js for interactive graph display
- **Responsive Design**: Mobile-friendly interface

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm start
```

### Database Schema

The system uses SQLite with the following main tables:
- `users`: User accounts and authentication
- `documents`: Uploaded file metadata and content
- `ontologies`: AI-generated or custom ontologies
- `extractions`: Structured data extraction results
- `session_tokens`: JWT token management

## Configuration

### Environment Variables

Backend (`backend/.env`):
```env
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-key
DATABASE_URL=sqlite:///./data/deepinsight.db
MAX_FILE_SIZE=104857600  # 100MB
```

Frontend (`frontend/.env.local`):
```env
REACT_APP_API_URL=http://localhost:8000
```

## Security

- Password requirements: 8+ chars, uppercase, lowercase, number, special character
- JWT token authentication with configurable expiration
- File type validation and size limits
- SQL injection prevention with SQLAlchemy ORM
- CORS protection for API endpoints

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

1. Set up Python environment on server
2. Configure environment variables for production
3. Set up reverse proxy (nginx) for frontend
4. Use PostgreSQL for production database
5. Configure SSL certificates

## Troubleshooting

### Common Issues

1. **Anthropic API Key Missing**
   - Add your API key to `backend/.env`
   - Restart the backend server

2. **File Upload Fails**
   - Check file size (max 100MB)
   - Ensure file type is supported (PDF, DOCX, TXT, MD)

3. **Database Issues**
   - Delete `backend/data/deepinsight.db` to reset
   - Restart backend to recreate tables

4. **Frontend Connection Issues**
   - Ensure backend is running on port 8000
   - Check CORS configuration in `main.py`

### Getting Help

1. Check the API documentation at http://localhost:8000/docs
2. Review browser console for frontend errors
3. Check backend logs in terminal
4. Ensure all dependencies are installed correctly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## System Requirements

### Minimum Requirements
- 4GB RAM
- 10GB disk space
- Python 3.8+
- Node.js 16+

### Recommended
- 8GB+ RAM
- 50GB+ disk space
- Python 3.10+
- Node.js 18+
- SSD storage for better performance

## Performance Notes

- Document processing time depends on file size and complexity
- AI ontology creation takes 30-60 seconds per document
- Data extraction scales with document size and ontology complexity
- Export generation is typically under 10 seconds

## Future Enhancements

- [ ] Real-time collaboration features
- [ ] Advanced graph visualization
- [ ] Batch document processing
- [ ] Custom AI model fine-tuning
- [ ] Integration with more graph databases
- [ ] Advanced search and filtering
- [ ] Document versioning
- [ ] API rate limiting and caching