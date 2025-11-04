# 📄 PDF Page Reconstructor

An intelligent AI-powered system that automatically reorders shuffled PDF pages back to their original logical sequence using multiple ordering strategies including page number detection, business logic rules, semantic analysis, and LLM reasoning.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120.4-green.svg)
![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 Overview

This project tackles the challenging problem of reconstructing shuffled PDF documents by intelligently analyzing page content and determining the correct logical order. It's particularly designed for legal and financial documents like loan agreements, mortgages, and contracts.

### Key Features

- **🤖 Multi-Strategy Ordering**: Uses 6 different strategies to determine page order
- **📊 Confidence Scoring**: Each ordering decision comes with a confidence score
- **🔍 OCR Fallback**: Handles scanned PDFs using Tesseract OCR
- **📝 Configurable Rules**: JSON-based document type definitions for business logic
- **🎨 Modern UI**: React-based frontend with real-time processing logs
- **⚡ Fast Processing**: Efficient PDF manipulation with PyMuPDF and PyPDF2
- **🌐 RESTful API**: Clean FastAPI backend with CORS support

---

## 🏗️ Architecture

### Backend (FastAPI + Python)

```
BE/
├── app.py                    # Main FastAPI application
├── services/
│   ├── pdf_svc.py           # PDF manipulation (extract, reorder)
│   ├── ocr_svc.py           # OCR fallback for scanned PDFs
│   ├── ordering_svc.py      # Orchestrator for ordering strategies
│   ├── strategies.py        # 6 ordering strategy implementations
│   └── doc_rules.json       # Document type definitions & rules
└── requirements.txt         # Python dependencies
```

### Frontend (React + TypeScript)

```
FE/
├── src/
│   ├── pages/
│   │   └── Index.tsx        # Main upload & display page
│   ├── components/
│   │   ├── PDFUpload.tsx    # File upload component
│   │   ├── PDFViewer.tsx    # Side-by-side PDF comparison
│   │   ├── ProcessingLogs.tsx   # Processing details display
│   │   └── TerminalLogs.tsx     # Backend logs display
│   └── components/ui/       # shadcn/ui components
├── package.json
└── vite.config.ts
```

---

## 🧠 Ordering Strategies

The system employs six intelligent strategies to determine page order:

### 1. **PageNumberStrategy** (Priority: Highest)
- Detects explicit page numbers using regex patterns
- Handles formats like: `-7-`, `page 7`, `7 of 20`, `p.7`
- Confidence: Up to 95% with good coverage

### 2. **ConfigurableBusinessLogicStrategy**
- Uses JSON-defined rules to classify document sections
- Auto-detects document type (loan agreement, mortgage, etc.)
- Matches patterns like "ARTICLE - I", "Schedule VI", "Signature"
- Confidence: Based on classification success rate

### 3. **StructuralPatternStrategy**
- Analyzes document structure (headers, footers, signatures)
- Identifies title pages, signature pages, and content density
- Confidence: Based on structural distinctiveness

### 4. **SemanticSimilarityStrategy**
- Uses sentence transformers (all-MiniLM-L6-v2) for embeddings
- Orders pages based on semantic flow
- Confidence: Based on consecutive page similarity

### 5. **DateSequenceStrategy**
- Detects and orders by chronological dates in content
- Handles multiple date formats
- Confidence: 70% when sufficient dates found

### 6. **LLMReasoningStrategy** (Gemini)
- Uses Google Gemini 2.5 Flash for advanced reasoning
- Analyzes page summaries and determines logical order
- Fallback when other strategies are uncertain

The **Orchestrator** runs all applicable strategies and selects the one with highest confidence.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 18+** and **npm/yarn**
- **Tesseract OCR** (for scanned PDFs)
- **Google Gemini API Key** (optional, for LLM strategy)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/pdf-reconstructor.git
cd pdf-reconstructor
```

#### 2. Backend Setup

```bash
cd BE

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Install Tesseract OCR

**Windows:**
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install and add to PATH
```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### 4. Configure Environment Variables

Create a `.env` file in the `BE/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Note:** The Gemini API key is optional. If not provided, the LLM strategy will be skipped.

#### 5. Frontend Setup

```bash
cd ../FE

# Install dependencies
npm install

# or with yarn
yarn install
```

---

## 🎮 Running the Application

### Start Backend Server

```bash
cd BE
python app.py
```

The backend will start on `http://localhost:8000`

**Available endpoints:**
- `GET /` - Health check
- `POST /reconstruct` - Upload and reconstruct PDF

### Start Frontend Development Server

```bash
cd FE
npm run dev
```

The frontend will start on `http://localhost:8080`

### Access the Application

Open your browser and navigate to:
```
http://localhost:8080
```

---

## 📖 Usage Guide

### Basic Usage

1. **Upload PDF**: Click "Select PDF File" or drag-and-drop a shuffled PDF
2. **Process**: Click "Upload & Reconstruct"
3. **View Results**: 
   - Original PDF displayed on the left
   - Reconstructed PDF displayed on the right
   - Processing logs shown in terminal-style output
4. **Download**: The reconstructed PDF is automatically downloaded

### Save Options

The application supports two save modes:

1. **Download to Browser** (Default)
   - PDF downloads directly to your browser's download folder

2. **Save to Custom Location**
   - Specify a full file path (e.g., `/home/user/Documents/reordered.pdf`)
   - File is saved directly to that location on the server
   - Useful for automated workflows

---

## 🔧 Configuration

### Document Rules (`BE/services/doc_rules.json`)

Define custom document types and their section patterns:

```json
{
  "document_types": {
    "your_doc_type": {
      "name": "Your Document Type",
      "sections": [
        {
          "name": "cover_page",
          "priority": 1,
          "weight": 2.0,
          "indicators": ["title", "company name"],
          "required_any": ["title"],
          "boost_patterns": ["^title.*company"]
        }
      ]
    }
  }
}
```

**Fields:**
- `priority`: Lower numbers appear first (1 = first)
- `weight`: Importance multiplier for scoring
- `indicators`: Keywords to look for
- `required_any`: At least one must match
- `boost_patterns`: Regex patterns for stronger matches

### Adding New Strategies

Extend `strategies.py`:

```python
class YourCustomStrategy(BaseOrderingStrategy):
    def __init__(self):
        super().__init__(threshold=0.6)
    
    def attempt_ordering(self, page_contents: List[Dict]) -> OrderingResult:
        # Your logic here
        return OrderingResult(
            order=[0, 1, 2, ...],
            confidence=0.85,
            reasoning=["Explanation of ordering"],
            method="your_strategy_name"
        )
```

Register in `ordering_svc.py`:

```python
def _initialize_strategies(self) -> List:
    return [
        PageNumberStrategy(),
        YourCustomStrategy(),  # Add here
        # ... other strategies
    ]
```

---

## 🧪 Testing

### Test with Sample PDFs

```bash
# Create a test directory
mkdir test_pdfs

# Add your shuffled PDFs
# Run the application and upload test files
```

### Backend API Testing

```bash
# Test health endpoint
curl http://localhost:8000/

# Test reconstruction endpoint
curl -X POST http://localhost:8000/reconstruct \
  -F "file=@/path/to/shuffled.pdf" \
  --output reconstructed.pdf
```

---

## 📊 API Reference

### POST `/reconstruct`

Reconstruct a shuffled PDF.

**Parameters:**
- `file` (form-data): PDF file to reconstruct
- `disposition` (query, optional): "inline" or "attachment" (default: "inline")
- `save_path` (form-data, optional): Custom save path on server

**Response Headers:**
- `X-Result-Meta`: JSON metadata about reconstruction
- `X-Backend-Logs`: URL-encoded array of processing logs
- `Content-Disposition`: Download filename

**Response Body:**
- Binary PDF data (when `save_path` not provided)
- JSON status (when `save_path` provided)

**Example Response Metadata:**
```json
{
  "original_filename": "shuffled.pdf",
  "page_count": 25,
  "final_order": [0, 2, 1, 3, 4, ...],
  "confidences": [0.95, 0.92, 0.88, ...],
  "avg_confidence": 0.91
}
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. **Backend won't start**
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in app.py
```

#### 2. **OCR not working**
```bash
# Verify Tesseract installation
tesseract --version

# On Windows, ensure Tesseract is in PATH
# Add to PATH: C:\Program Files\Tesseract-OCR
```

#### 3. **Frontend can't connect to backend**
- Check CORS settings in `app.py`
- Ensure backend is running on `http://localhost:8000`
- Check browser console for errors

#### 4. **Low confidence scores**
- Check `doc_rules.json` patterns match your document type
- Add more specific indicators for your document sections
- Consider adjusting strategy weights

#### 5. **Out of memory errors**
- Large PDFs may cause memory issues
- Reduce PDF size or page count
- Increase system memory allocation

---

## 🔐 Security Considerations

⚠️ **Important Security Notes:**

1. **No Authentication**: This application has no authentication. Do not expose to public internet without adding security.

2. **File Upload Validation**: Only basic PDF validation is performed. In production:
   - Add file size limits
   - Implement virus scanning
   - Validate file contents thoroughly

3. **Path Traversal**: The `save_path` parameter accepts any path. In production:
   - Sanitize and validate paths
   - Restrict to specific directories
   - Implement access controls

4. **API Keys**: Never commit API keys to version control
   - Use environment variables
   - Use secrets management in production

5. **CORS**: Currently allows all origins. In production:
   - Restrict to specific domains
   - Implement proper CORS policies

---

## 📦 Dependencies

### Backend
- **FastAPI**: Web framework
- **PyMuPDF (fitz)**: PDF text extraction
- **PyPDF2**: PDF manipulation
- **pytesseract**: OCR for scanned PDFs
- **sentence-transformers**: Semantic embeddings
- **google-generativeai**: Gemini LLM integration
- **scikit-learn**: ML utilities
- **rich**: Terminal formatting

### Frontend
- **React**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **shadcn/ui**: UI components
- **Tailwind CSS**: Styling
- **react-pdf**: PDF viewing
- **axios**: HTTP client

---

## 🚧 Future Enhancements

- [ ] Multi-document batch processing
- [ ] Support for more document types
- [ ] Machine learning model training on successful reconstructions
- [ ] User feedback mechanism to improve strategies
- [ ] Docker containerization
- [ ] Cloud deployment support (AWS, GCP, Azure)
- [ ] Advanced analytics dashboard
- [ ] Support for other file formats (DOCX, PPTX)
- [ ] Collaborative document review features
- [ ] API rate limiting and authentication

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style
- Backend: Follow PEP 8
- Frontend: Follow Airbnb React/TypeScript style guide
- Add comments for complex logic
- Write meaningful commit messages

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work*

---

## 🙏 Acknowledgments

- **PyMuPDF** for excellent PDF handling
- **Tesseract OCR** for optical character recognition
- **Sentence Transformers** for semantic embeddings
- **Google Gemini** for LLM capabilities
- **shadcn/ui** for beautiful UI components
- **FastAPI** for the modern web framework

---

## 📞 Support

For support, email your.email@example.com or open an issue in the GitHub repository.

---

## 📈 Project Status

🚀 **Active Development** - This project is actively maintained and accepting contributions.

**Current Version:** 1.0.0

**Last Updated:** November 2025

---

## 🔗 Links

- **Documentation**: [GitHub Wiki](https://github.com/yourusername/pdf-reconstructor/wiki)
- **Issue Tracker**: [GitHub Issues](https://github.com/yourusername/pdf-reconstructor/issues)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

Made with ❤️ by [Your Name]