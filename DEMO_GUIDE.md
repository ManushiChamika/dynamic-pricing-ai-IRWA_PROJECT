# FluxPricer AI - Week 6 Mid-Evaluation Demo Guide

## Quick Start

### Running the Application
```bash
# Navigate to project directory
cd "C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT"

# Run with Python 3.11 (required for dependencies)
py -3.11 -m streamlit run app/streamlit_app.py --server.port=8505
```

**Demo URL**: http://localhost:8505

## Demo Flow & Key Features

### 1. **Landing Page** 🚀
- **URL**: http://localhost:8505/?page=landing
- **Purpose**: Professional entry point showcasing FluxPricer AI capabilities
- **Features**:
  - Modern UI design from `ui-rewrite` branch integration
  - Feature highlights (AI-Powered Intelligence, Lightning Fast, Revenue Maximization)
  - Multi-Agent AI System overview
  - Call-to-action buttons to enter dashboard

### 2. **Multi-Agent System Showcase** 🤖

#### **Dashboard** (Main Hub)
- **URL**: http://localhost:8505/?page=dashboard
- **Features**:
  - Real-time pricing metrics
  - Dynamic pricing data visualization
  - User session management
  - Integration with all agent services

#### **AI Assistant** (UserInteractionAgent)
- **Navigation**: Dashboard → AI Assistant
- **Features**:
  - Natural language chat interface
  - Direct integration with `core.agents.user_interact.UserInteractionAgent`
  - Conversational pricing insights
  - LLM-powered responses

#### **Activity Monitor** (System Intelligence)
- **Navigation**: Dashboard → Activity
- **Features**:
  - Real-time system activity logs
  - Agent execution monitoring
  - Incident tracking and resolution
  - Multi-agent coordination display

#### **Alerts & Notifications** (Alert Service Agent)
- **Navigation**: Dashboard → Alerts
- **Features**:
  - Real-time alert streaming
  - Integration with `core.agents.alert_service`
  - Background asyncio processing
  - Notification badge system

#### **Price Proposals** (Pricing Optimizer Agent)
- **Navigation**: Dashboard → Proposals
- **Features**:
  - AI-generated pricing recommendations
  - Price optimization proposals
  - Integration with pricing optimizer agent
  - Approval/rejection workflow

### 3. **Technical Architecture Highlights**

#### **Multi-Agent System Integration**
- **Data Collector Agents**: Market intelligence gathering
- **Price Optimizer**: ML-powered pricing algorithms  
- **Alert Service**: Real-time monitoring and notifications
- **User Interaction Agent**: Natural language interface
- **Policy Guard**: Business rule compliance

#### **Advanced Features**
- **Async Processing**: Background loops for real-time updates
- **Session Management**: Secure user authentication
- **Database Integration**: SQLite with proper initialization
- **Theme System**: Professional UI theming
- **Query Parameter Routing**: Modern navigation system

## Academic Project Compliance ✅

### **Multi-Agent System Requirements**
- ✅ **Multiple Specialized Agents**: Data Collector, Price Optimizer, Alert Service, User Interaction
- ✅ **Agent Communication**: Message bus system with async processing
- ✅ **Real-time Processing**: Live alerts, activity monitoring, chat interface
- ✅ **Intelligent Decision Making**: AI-powered pricing optimization
- ✅ **User Interface**: Professional web-based dashboard

### **Technical Sophistication**
- ✅ **Machine Learning Integration**: LLM for chat, pricing algorithms
- ✅ **Asynchronous Processing**: Background loops, concurrent agent execution
- ✅ **Database Management**: Proper data persistence and session handling
- ✅ **Modern Web Framework**: Streamlit with advanced routing
- ✅ **Professional UI/UX**: Integrated theme system and responsive design

### **Integration Quality**
- ✅ **Backward Compatibility**: All existing functionality preserved
- ✅ **Safe Integration**: Risk assessment and component isolation
- ✅ **Documentation**: Comprehensive analysis and guides
- ✅ **Testing**: Multiple test environments and validation

## Troubleshooting

### **Dependency Issues**
- **Problem**: `ModuleNotFoundError: No module named 'werkzeug'`
- **Solution**: Use Python 3.11 explicitly: `py -3.11 -m streamlit run app/streamlit_app.py`

### **Port Conflicts**
- **Alternative Ports**: 8505 (recommended), 8503, 8504
- **Kill Existing**: `taskkill /f /im streamlit.exe`

### **Navigation**
- **Landing Page**: Add `?page=landing` to URL
- **Dashboard**: Add `?page=dashboard` to URL
- **Home**: Default URL without parameters

## Demo Script for Evaluation

1. **Start with Landing Page** - Show professional UI and feature overview
2. **Navigate to Dashboard** - Demonstrate main application hub
3. **AI Assistant Demo** - Show natural language interaction with agents
4. **Activity Monitor** - Display real-time agent coordination
5. **Alerts System** - Show live notification system
6. **Price Proposals** - Demonstrate AI-powered pricing recommendations

**Total Demo Time**: 10-15 minutes
**Key Message**: Sophisticated multi-agent AI system with professional user interface

---
*Last Updated: September 25, 2025*
*Branch: dev-enhanced*
*Integration Status: COMPLETE ✅*