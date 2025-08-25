# AI-Assisted Brand Color Extraction for Onboarding Acceleration

An intelligent web application that automatically extracts brand colors from websites using advanced AI techniques, designed to streamline the email template customization process for marketing platforms.

## Overview

This proof-of-concept application addresses the challenge of brand color extraction from websites by combining web scraping, computer vision, and multimodal AI. Users can input any website URL and receive an accurate brand color palette that can be used to customize email templates automatically.

The system employs a sophisticated multi-method approach, culminating in a hybrid solution that uses multimodal LLM reasoning combined with color quantization for optimal accuracy and precision.

## Tech Stack

### Backend
- **Python** - Core backend language
- **FastAPI** - Modern, fast web framework for building APIs
- **Playwright** - Automated browser control for webpage rendering and screenshots
- **ColorThief** - Color quantization and palette extraction
- **OpenAI GPT-4.1** - Multimodal LLM for intelligent color selection
- **Pydantic** - Data validation and serialization

### Frontend
- **Next.js 15** - React framework with server-side rendering
- **React 19** - User interface library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS 4** - Utility-first CSS framework

### Infrastructure
- **Docker** - Containerization for consistent deployment
- **Docker Compose** - Multi-container orchestration

## Setup Guide

### Prerequisites

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **OpenAI API Key** - Required for AI-powered color analysis

### Environment Configuration

1. **Clone the repository**
   ```bash
   git clone https://github.com/chienpb/email-template-branding.git
   ```

2. **Create environment configuration**
   
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   Replace `your_openai_api_key_here` with your actual OpenAI API key.

### Running with Docker

#### Development Environment

1. **Start the application**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

#### Production Environment

1. **Start the application**
   ```bash
   docker-compose up --build -d
   ```

2. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Stopping the Application

```bash
# For development
docker-compose -f docker-compose.dev.yml down

# For production
docker-compose down
```

### Health Checks

The backend includes built-in health checks. You can verify the system status:

```bash
curl http://localhost:8000/health
```

## Usage

1. **Open the application** in your browser at http://localhost:3000
2. **Enter a website URL** in the input field
3. **Click "Extract Brand Colors"** to analyze the website



## Architecture

The application follows a simple architecture with containerized frontend and backend services. The backend orchestrates multiple color extraction methods and uses AI reasoning to determine the most representative brand colors from website screenshots and extracted palettes.

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your OpenAI API key is correctly set in `config.env`
2. **Port Conflicts**: If ports 3000 or 8000 are in use, modify the port mappings in `docker-compose.yml`
3. **Browser Dependencies**: The Playwright browser dependencies are automatically installed in the Docker container
