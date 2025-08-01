# Research Brief Generator - Streamlit Frontend

A beautiful, interactive web interface for the Context-Aware Research Brief Generator built with Streamlit.

## 🚀 Features

### 💬 Conversation Interface
- **Chat-like experience** for research queries
- **Real-time brief generation** with progress indicators
- **Context-aware responses** with follow-up support
- **Trace links** to LangSmith monitoring

### 📋 Brief Generator
- **Structured form** for research brief generation
- **Multiple depth options** (shallow, moderate, deep)
- **Advanced options** for additional context
- **Tabbed results** with executive summary, analysis, sources, and metrics

### 📊 History & Statistics
- **User statistics** with key metrics
- **Research history** with expandable briefs
- **Performance tracking** over time

### 🔍 System Monitoring
- **Real-time health checks**
- **System configuration** display
- **Monitoring status** from LangSmith

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Backend API running (see backend README)

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements-frontend.txt
   ```

2. **Start the backend** (in backend directory):
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

3. **Start the frontend**:
   ```bash
   streamlit run frontend.py
   ```

4. **Open your browser** to `http://localhost:8501`

## 🎯 Usage

### Conversation Tab
1. **Enter your research question** in the chat input
2. **Configure options** in the sidebar:
   - User ID
   - Research depth
   - Follow-up context
   - Additional context
3. **Click Send** to generate a research brief
4. **View results** in the chat interface with trace links

### Brief Generator Tab
1. **Fill out the form**:
   - Research topic
   - Depth level
   - Follow-up options
   - Advanced context (optional)
2. **Click Generate** to create a comprehensive brief
3. **Explore results** in organized tabs:
   - Executive Summary
   - Detailed Analysis
   - Research Sources
   - Performance Metrics

### History & Stats Tab
- **View user statistics** including total briefs, sources, and execution times
- **Browse research history** with expandable brief details
- **Track performance** over time

### Monitoring Tab
- **Check system health** and configuration
- **View monitoring status** from LangSmith
- **Monitor API endpoints**

## 🎨 Interface Features

### Responsive Design
- **Wide layout** for better content display
- **Custom CSS styling** for professional appearance
- **Mobile-friendly** responsive design

### Visual Elements
- **Color-coded messages** (user vs assistant)
- **Progress indicators** during generation
- **Metric cards** for statistics
- **Expandable sections** for detailed views

### User Experience
- **Real-time feedback** with spinners and status messages
- **Error handling** with helpful error messages
- **Session persistence** for chat history
- **Sidebar configuration** for easy access

## 🔧 Configuration

### API Connection
The frontend connects to the backend API at `http://localhost:8000`. To change this:

1. **Edit the API_BASE_URL** in `frontend.py`:
   ```python
   API_BASE_URL = "http://your-api-url:port"
   ```

2. **For production deployment**, update the URL to your deployed API endpoint.

### Customization
- **Modify CSS styles** in the `st.markdown` section
- **Add new tabs** by extending the tab structure
- **Customize metrics** in the statistics section

## 📊 Demo Scenarios

### Scenario 1: Initial Research
1. Go to **Conversation Tab**
2. Ask: "What are the latest trends in artificial intelligence?"
3. Configure: Depth = Moderate, Follow-up = Off
4. Generate and explore results

### Scenario 2: Follow-up Query
1. After Scenario 1, enable **Follow-up Query**
2. Ask: "How do these trends affect healthcare?"
3. Notice how context is incorporated

### Scenario 3: Deep Research
1. Go to **Brief Generator Tab**
2. Enter topic: "Quantum computing applications in cryptography"
3. Set depth to "Deep"
4. Add context: "Focus on practical implementations and security implications"
5. Generate comprehensive brief

### Scenario 4: Monitoring
1. Go to **Monitoring Tab**
2. Check system health and configuration
3. View LangSmith trace links from previous queries

## 🚀 Deployment

### Local Development
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Start frontend
streamlit run frontend.py
```

### Production Deployment
1. **Deploy backend** to cloud platform
2. **Update API_BASE_URL** in frontend
3. **Deploy frontend** to Streamlit Cloud or similar

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 🔍 Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify API health endpoint

2. **Generation Timeout**
   - Increase timeout in `generate_brief()` function
   - Check backend performance
   - Monitor LangSmith traces

3. **Styling Issues**
   - Clear browser cache
   - Check CSS syntax in `st.markdown`
   - Verify Streamlit version compatibility

### Debug Mode
```bash
# Run with debug information
streamlit run frontend.py --logger.level debug
```

## 📈 Performance

### Optimization Tips
- **Use moderate depth** for faster responses
- **Enable follow-up** for context-aware queries
- **Monitor execution times** in metrics tab
- **Check LangSmith traces** for performance insights

### Expected Performance
- **Shallow research**: 30-60 seconds
- **Moderate research**: 60-120 seconds
- **Deep research**: 120-300 seconds

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ using Streamlit, LangGraph, and LangChain** 