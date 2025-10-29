# Shopify AI Management App - Development Plan

## Current Status: Phase 3 Complete ✅ + Backend Error Fixes ✅

---

## Phase 1: AI Agent Infrastructure with Model Fallback ✅
**Goal**: Implement intelligent AI model selection with Ollama (local) as primary, OpenRouter as fallback, OpenAI as last resort

### Tasks:
- [x] Install Ollama Python SDK
- [x] Configure model priority system (Ollama → OpenRouter → OpenAI)
- [x] Create AI orchestrator with automatic fallback logic
- [x] Integrate Agno agent framework with DuckDuckGo tools
- [x] Add conversation history and context management
- [x] Build chat interface with streaming support
- [x] Fix import errors (use DuckDuckGoTools, correct model class names)

**Status**: ✅ COMPLETE
- AI model fallback working correctly (Ollama → OpenRouter → OpenAI)
- Chat interface fully functional at `/chat` route
- Agent initialized with DuckDuckGo search tools
- Streaming response support implemented
- Conversation history management working

---

## Phase 2: Shopify API Integration & Settings Page ✅
**Goal**: Build Settings page for API credentials and connect to Shopify Admin GraphQL API

### Tasks:
- [x] Create SettingsState for managing credentials (Shopify, OpenAI, OpenRouter)
- [x] Build Settings page UI for credential configuration
- [x] Add password visibility toggles for API keys
- [x] Implement credential validation indicators
- [x] Install Shopify Python SDK (ShopifyAPI)
- [x] Implement GraphQL client for Admin API
- [x] Create ShopifyState with connection testing
- [x] Add error handling for API rate limits and auth failures
- [x] Add AI model API key testing functionality
- [x] Create AIModelState for testing OpenAI and OpenRouter keys
- [x] Add individual "Test Key" buttons for each AI model
- [x] Display success/error indicators for API key validation

**Status**: ✅ COMPLETE
- Settings page fully functional at `/settings` route
- Shopify credentials management implemented
- AI model API key configuration (OpenAI, OpenRouter)
- AI model key testing with visual feedback ✅
- Shopify connection testing with visual feedback
- GraphQL client ready for queries

---

## Phase 3: Core Shopify Tools for AI Agent ✅
**Goal**: Expose Shopify operations as callable tools for the AI agent

### Product Management Tools:
- [x] `get_products` - Retrieve all products or search by title
- [x] `get_product_by_id` - Fetch specific product details
- [x] `create_product` - Add new products to store

### Customer Management Tools:
- [x] `get_customers` - Search customers by name/email
- [x] `update_customer` - Modify customer information
- [x] `get_customer_orders` - View customer order history

### Order Management Tools:
- [x] `get_orders` - Retrieve orders with filtering
- [x] `get_order_by_id` - Get specific order details
- [x] `update_order` - Modify order information

### Integration:
- [x] Create ShopifyTools class for Agno agent
- [x] Connect tools to ChatState
- [x] Add error handling for API failures
- [x] **FIX**: Change agent.run() to agent.arun() for async tool support
- [x] **FIX**: Add stream=True parameter to enable response streaming
- [x] **FIX**: Extract content from RunContentEvent objects properly
- [x] **FIX**: Fix Ollama import error (RequestError instead of ConnectError)

**Status**: ✅ COMPLETE
- All 9 Shopify tools implemented and registered
- ShopifyTools integrated with Agno agent
- Tools conditionally loaded based on credential availability
- GraphQL queries working for products, customers, and orders
- Proper error handling and session management
- **Async tool support fully functional** ✅
- **Streaming responses working correctly** ✅
- **All import errors resolved** ✅

---

## Backend Fixes Applied ✅

### Issue: "Async tool shopify can't be used with synchronous agent.run()"

**Root Cause**: ShopifyTools methods are async, but ChatState was using synchronous `agent.run()`

**Fixes Applied**:
1. ✅ Changed `self._agent.run()` to `self._agent.arun()` to support async tools
2. ✅ Added `stream=True` parameter to enable proper streaming: `agent.arun(..., stream=True)`
3. ✅ Fixed streaming iteration to handle `RunContentEvent` objects properly
4. ✅ Fixed Ollama import error: changed `ConnectError` to `RequestError`

**Testing Results**:
- ✅ Agent initialization works without errors
- ✅ Streaming responses work correctly with async tools
- ✅ Shopify tools can now be called by the AI agent
- ✅ Ollama fallback logic works properly
- ✅ Full chat flow tested and verified

---

## Phase 4: Custom Dashboard with KPI Widgets
**Goal**: Create customizable dashboard with real-time Shopify metrics

### Tasks:
- [ ] Build widget system (drag-and-drop layout)
- [ ] Implement KPI cards (24hr order value, AOV, conversion rate)
- [ ] Add time-based comparisons (this week vs last week)
- [ ] Create chart components for sales trends
- [ ] Enable widget customization (add/remove/reorder)

---

## Phase 5: PDF Report Generation
**Goal**: Export key metrics and data as formatted PDF reports

### Tasks:
- [ ] Install ReportLab or similar PDF library
- [ ] Design PDF templates for different report types
- [ ] Implement data aggregation for reports
- [ ] Add export functionality to dashboard
- [ ] Include charts and visualizations in PDFs

---

## Phase 6: Testing & Polish
**Goal**: Comprehensive testing and UI/UX improvements

### Tasks:
- [ ] Test AI agent with various query complexities
- [ ] Verify model fallback chain works correctly
- [ ] Test all Shopify tools with real store data
- [ ] UI/UX refinements based on testing
- [ ] Performance optimization for large datasets

---

## Implementation Summary:

### ✅ Completed Features:
1. **AI Agent with Model Fallback** (Ollama → OpenRouter → OpenAI)
2. **Settings Page** with credential management and connection testing
3. **9 Shopify Tools** for product, customer, and order management
4. **Agno Integration** with DuckDuckGo and Shopify toolkits
5. **Chat Interface** with streaming responses and conversation history
6. **AI Model Key Testing** with OpenAI and OpenRouter validation
7. **Async Tool Support** for Shopify API integration ✅
8. **Backend Error Fixes** for streaming and imports ✅

### 🔧 Recent Fixes:
- **Async Tool Error**: Fixed by changing `agent.run()` to `agent.arun(stream=True)`
- **Streaming Implementation**: Properly extracting content from `RunContentEvent` objects
- **Ollama Import Error**: Changed `ConnectError` to `RequestError`

### 📊 Technical Details:
- **Shopify Tools**: 9 async tools using GraphQL Admin API
- **AI Models**: 3-tier fallback system (Ollama, OpenRouter, OpenAI)
- **Chat Framework**: Agno with async tool calling support
- **API Integration**: ShopifyAPI v12.7.0 with GraphQL
- **Streaming**: Real-time response streaming with `arun(stream=True)`
