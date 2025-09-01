# React Migration - Development Guide

This document covers the new React + FastAPI architecture for the BREAKthrough OM Screening Platform.

## Architecture Overview

**Migration Status**: 🚧 Phase 1 Complete - Basic structure implemented

### New Structure (Monolithic Deployment)
```
bio-hit-finder/
├── frontend/           # React application  
│   ├── src/
│   │   ├── components/   # Modern UI components (shadcn/ui)
│   │   ├── hooks/       # React Query hooks for API
│   │   ├── lib/         # API client and utilities  
│   │   └── pages/       # Page components
│   └── package.json     # React dependencies
├── backend/            # FastAPI application
│   ├── main.py         # FastAPI app + static file serving
│   ├── core/           # Existing Python modules (unchanged)
│   ├── analytics/      # Statistical analysis modules (unchanged)
│   └── requirements.txt # Python dependencies
├── build.py            # Production build script
├── dev.py              # Development server script
└── render.yaml         # Render deployment configuration
```

## Development Setup

### Quick Start
```bash
# Install frontend dependencies
cd frontend && npm install && cd ..

# Install backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Run both servers
python dev.py
```

### Manual Development
```bash
# Terminal 1: Backend (FastAPI)
cd backend && python main.py
# Serves API at http://localhost:8000/api

# Terminal 2: Frontend (React + Vite)  
cd frontend && npm run dev
# Serves React app at http://localhost:5173
```

### Testing the Integration
1. Visit http://localhost:5173 (React dev server)
2. Check the connection badge in the hero section
3. Should show "Backend Connected" if FastAPI is running

## Current Implementation Status

### ✅ Completed (Phase 1)
- [x] Monolithic project structure (React + FastAPI)
- [x] React component integration from spark-inspiration-browse  
- [x] FastAPI backend with static file serving
- [x] API client with React Query integration
- [x] Connection status indicator in UI
- [x] Development and build scripts
- [x] Render deployment configuration

### 🚧 In Progress (Phase 2)
- [ ] File upload API implementation
- [ ] Data processing API endpoints
- [ ] Enhanced React components for scientific workflows
- [ ] Integration with existing Python analysis modules

### 📅 Planned (Phase 3+)
- [ ] Interactive heatmap components  
- [ ] Multi-stage hit calling UI
- [ ] Real-time processing updates
- [ ] Export functionality integration
- [ ] Performance optimization

## API Endpoints

### Currently Available
- `GET /api/health` - Health check endpoint
- `GET /api/v1/test` - Test endpoint returning simple message

### Planned Implementation
```python
# File Upload & Processing
POST /api/v1/upload           # Upload CSV/Excel files
POST /api/v1/process/{id}     # Start analysis job
GET  /api/v1/jobs/{id}/status # Processing status

# Analysis Results
GET  /api/v1/analysis/{id}/summary    # Summary statistics
GET  /api/v1/analysis/{id}/data       # Processed data with pagination
GET  /api/v1/analysis/{id}/hits       # Hit calling results

# Visualization Data
GET  /api/v1/analysis/{id}/heatmap/{metric}  # Plate heatmap data
GET  /api/v1/analysis/{id}/distributions     # Chart data
GET  /api/v1/analysis/{id}/qc               # Quality control metrics

# Export
POST /api/v1/analysis/{id}/export     # Generate exports
GET  /api/v1/exports/{id}/download    # Download ZIP bundle
```

## Component Enhancement Plan

### Enhanced Components Needed

1. **Scientific Data Upload**
   - Multi-file upload with drag & drop
   - Excel sheet detection and selection  
   - Column mapping and validation
   - Processing parameter configuration

2. **Interactive Analysis Dashboard**
   - Real-time processing status
   - Key metrics display
   - Parameter adjustment controls
   - Stage-based workflow navigation

3. **Advanced Visualizations**
   - Custom plate heatmap (96/384-well layouts)
   - Interactive statistical charts
   - Quality control dashboard
   - Export-quality rendering

4. **Scientific Workflow Components**
   - Multi-stage hit calling interface
   - B-scoring parameter controls
   - Edge effect detection display
   - Statistical interpretation guides

## Deployment

### Local Production Build
```bash
python build.py
cd backend && python main.py
# Visit: http://localhost:8000 (serves both API and React)
```

### Render Deployment
1. Push to `feature/react-migration` branch
2. Connect GitHub repo to Render
3. Render detects `render.yaml` and builds automatically:
   - Installs Node.js → builds React app
   - Installs Python deps → starts FastAPI server
   - Single URL serves entire application

### Environment Variables
```bash
# Render dashboard settings
PYTHON_VERSION=3.11.0
NODE_VERSION=18
```

## Benefits of New Architecture

### vs. Original Streamlit App
- **Modern UI**: Professional, responsive design with shadcn/ui
- **Better Performance**: Client-side caching, optimized bundling
- **API Access**: External integrations possible
- **Deployment Flexibility**: Not limited to Streamlit Cloud

### Maintained Features
- **All statistical algorithms**: Core Python modules unchanged
- **Calculation accuracy**: Numerical precision preserved  
- **Feature completeness**: All original functionality planned
- **Scientific rigor**: Methodology documentation included

## Migration Philosophy

**Gradual Enhancement**: Preserve what works, modernize what needs improvement.

The existing Python core (calculations, statistics, analysis) is **excellent** and remains unchanged. We're building a modern React UI around this proven scientific foundation while adding API access for future integrations.

## Next Development Steps

1. **Implement File Upload API** - Connect DataUpload component to backend
2. **Port Statistical Analysis** - Create API endpoints for existing algorithms  
3. **Build Interactive Heatmaps** - Custom SVG-based plate visualizations
4. **Add Real-time Updates** - WebSocket integration for processing status
5. **Optimize Performance** - Caching, bundling, deployment tuning

This migration maintains scientific accuracy while providing a foundation for modern features and integrations.