# Shopify AI Management App - Refactored Plan

## 🎯 NEW DIRECTION: Cloud-Only AI Models + Enhanced Shopify Tools

**Decision**: Remove Ollama (local model) support entirely. Focus on:
1. Cloud-based AI models (Mistral AI primary, OpenRouter secondary, OpenAI fallback)
2. Better encoding Shopify API permissions as vLLM/vSLM-friendly tools
3. Improved tool descriptions and structured outputs
4. Intelligent agent instructions and context
5. **Full Shopify Admin + Storefront API support**

---

## Phase 1: Remove Ollama & Simplify Model Selection ✅
**Goal**: Strip out all Ollama-related code and create clean OpenRouter → OpenAI fallback

### Tasks:
- [x] Remove `ollama` package from requirements.txt
- [x] Remove Ollama import and availability check from AIOrchestrator
- [x] Simplify model selection to: OpenRouter (primary) → OpenAI (fallback)
- [x] Remove `_is_ollama_available()` method entirely
- [x] Update `get_best_model()` to only check cloud API keys
- [x] Remove all Ollama-related error logging
- [x] Update model display names to show only cloud options
- [x] Test fallback chain: OpenRouter → OpenAI → No model available

**Status**: ✅ COMPLETE

---

## Phase 2: Enhance Shopify Tools for vLLM/vSLM Compatibility ✅
**Goal**: Rewrite Shopify tools with better descriptions, examples, and structured schemas

### Tasks:
- [x] Add detailed docstrings with usage examples for each tool
- [x] Add parameter validation and type hints
- [x] Include permission requirements in tool descriptions
- [x] Add example queries that demonstrate proper tool usage
- [x] Add tool categorization (Product/Customer/Order Management)
- [x] Test tools with Agno agent
- [x] Verify backward compatibility

**Status**: ✅ COMPLETE

---

## Phase 3: Improve AI Agent Instructions & Context ✅
**Goal**: Add system prompts and context to help AI understand Shopify operations

### Tasks:
- [x] Create Shopify-specific system instructions for agent
- [x] Add context about common Shopify operations
- [x] Define tool usage patterns and best practices
- [x] Add examples of complex multi-tool workflows
- [x] Include GraphQL ID format guidance (gid://shopify/Resource/ID)
- [x] Add error recovery patterns for failed API calls

**Status**: ✅ COMPLETE

---

## Phase 4: Add Mistral AI Integration ✅
**Goal**: Integrate Mistral AI as the primary model provider with native Agno support

### Tasks:
- [x] Install `mistralai` Python SDK package
- [x] Add `MISTRAL_API_KEY` to settings state and UI
- [x] Create Mistral model initialization in AIOrchestrator
- [x] Update model priority: Mistral → OpenRouter → OpenAI
- [x] Add Mistral API key test functionality in AIModelState
- [x] Update settings page with Mistral API key input field
- [x] Test Agno agent with MistralChat model
- [x] Verify streaming responses work with Mistral
- [x] Update current_model_name display to show Mistral

**Status**: ✅ COMPLETE

**Results**:
- Successfully installed `mistralai` SDK package
- Added Mistral API key management in SettingsState
- Implemented Mistral API key testing in AIModelState
- Updated AIOrchestrator with Mistral as primary model (mistral-large-latest)
- Verified fallback chain: Mistral → OpenRouter → OpenAI → No model available
- Settings page now includes Mistral API key input with visibility toggle
- Chat interface displays current model name correctly
- All tests passed: model selection, fallback logic, and UI integration

**Implementation Summary**:
- **SDK**: `mistralai` package installed and working
- **Agno Integration**: Uses `agno.models.mistral.MistralChat` class
- **Model ID**: `"mistral-large-latest"` for best performance
- **API Key**: Stored in `MISTRAL_API_KEY` environment variable
- **Priority Chain**: Mistral (1st) → OpenRouter (2nd) → OpenAI (3rd) → None
- **UI**: Mistral section added to settings page with test functionality

---

## Phase 4.5: Add Shopify Storefront API Integration ✅
**Goal**: Enable full Shopify Storefront API support alongside Admin API

### Tasks:
- [x] Add `SHOPIFY_STOREFRONT_TOKEN` to SettingsState with env var loading
- [x] Add visibility toggle for storefront token in settings
- [x] Create computed var `is_shopify_storefront_token_set` to check token status
- [x] Add Storefront API section to settings page UI
- [x] Implement "Test Storefront Token" functionality in AIModelState
- [x] Add `_test_shopify_storefront()` method using GraphQL shop query
- [x] Add storefront testing UI with spinner and success/error display
- [x] Update ChatState to check storefront token availability
- [x] Expose storefront API status to AI agent via system context
- [x] Document storefront token requirement in ShopifyTools

**Status**: ✅ COMPLETE

**Implementation Details**:
- **SettingsState**: Added `shopify_storefront_token` field with `is_shopify_storefront_token_set` computed var
- **AIModelState**: Implemented `_test_shopify_storefront()` that validates token using GraphQL API
- **Settings UI**: New "Shopify Storefront API" section with input field, visibility toggle, and test button
- **Testing**: Uses `https://{store_url}/api/2024-04/graphql.json` endpoint with `X-Shopify-Storefront-Access-Token` header
- **ChatState**: AIOrchestrator can access storefront credentials and expose to agent tools
- **Environment Variable**: `SHOPIFY_STOREFRONT_TOKEN` loaded from .env file

**What This Enables**:
- Dual API support: Admin API for management operations, Storefront API for customer-facing queries
- Separate credential management for each API type
- Independent testing of Admin and Storefront connections
- AI agent can use appropriate API based on task requirements
- Future Storefront-specific tools (product catalog queries, cart operations, checkout flows)

---

## Phase 4.6: Create Shopify Storefront Tools ✅
**Goal**: Implement customer-facing Storefront API tools for the AI agent

### Tasks:
- [x] Create new `ShopifyStorefrontTools` toolkit class
- [x] Implement `search_products` tool for product catalog queries
- [x] Implement `get_product_by_handle` tool for detailed product info
- [x] Add vLLM/vSLM-friendly docstrings with usage examples
- [x] Use GraphQL queries via httpx with proper authentication
- [x] Add `[Storefront]` prefix to distinguish from Admin tools
- [x] Integrate tools into ChatState agent initialization
- [x] Update system prompt to guide agent on when to use each API
- [x] Test toolkit initialization and tool signatures

**Status**: ✅ COMPLETE

**Implementation Details**:
- **File Created**: `app/tools/shopify_storefront_tools.py`
- **Tools Implemented**:
  1. **search_products**: Search for products in the online store using keywords
  2. **get_product_by_handle**: Get public product details by URL handle
- **Architecture**:
  - Async methods throughout for non-blocking operations
  - GraphQL queries to Storefront API endpoint
  - Authentication via `X-Shopify-Storefront-Access-Token` header
  - Structured JSON responses with success/error handling
  - Comprehensive error logging
- **Agent Integration**:
  - Tools conditionally loaded when `is_shopify_storefront_token_set` is True
  - System prompt updated to explain Admin vs Storefront tool usage
  - Clear guidance: Admin for management, Storefront for customer-facing queries
  - Tools marked with `[Storefront]` prefix for easy identification

**What This Enables**:
- AI agent can now query public product catalog (what customers see)
- Check product availability from customer perspective
- Search products using customer-friendly terms
- Get detailed product information by handle (URL-friendly ID)
- Separate clear distinction between internal management and public-facing operations

---

## Phase 5: Custom Dashboard with KPI Widgets
**Goal**: Build visual dashboard with real-time Shopify metrics

### Tasks:
- [ ] Design dashboard layout with grid system
- [ ] Implement KPI widgets (24hr order value, AOV, conversion rate)
- [ ] Add time-based comparisons (this week vs last week)
- [ ] Create chart components for sales trends
- [ ] Enable widget customization (add/remove/reorder)

**Status**: ⏳ BACKLOG

---

## Phase 6: PDF Report Generation
**Goal**: Export key metrics as formatted PDF reports

### Tasks:
- [ ] Install ReportLab or similar PDF library
- [ ] Design PDF templates for different report types
- [ ] Implement data aggregation for reports
- [ ] Add export functionality to dashboard
- [ ] Include charts and visualizations in PDFs

**Status**: ⏳ BACKLOG

---

## 📊 Current Implementation Status

### ✅ What's Working:
- **Settings Management**:
  - Shopify Admin API credentials (store URL + access token)
  - Shopify Storefront API credentials (store URL + storefront token)
  - AI model API keys (Mistral, OpenRouter, OpenAI)
  - Credential visibility toggles
  - Independent testing for each API type
- **Shopify Integration**:
  - **9 Admin API tools** for management operations (Product/Customer/Order)
  - **2 Storefront API tools** for customer-facing queries (Product Search/Details)
  - Dual API architecture with clear separation of concerns
  - GraphQL-based queries with proper authentication
  - Intelligent error handling and recovery
- **AI Agent**:
  - Streaming responses with multiple AI models
  - Cloud-only model selection: Mistral → OpenRouter → OpenAI
  - Conversation history with markdown support
  - Processing status indicators
  - Agent-based architecture with Agno framework
  - **Intelligent tool routing** between Admin and Storefront APIs
  - System prompt guidance for appropriate tool selection
- **Chat Interface**:
  - Natural language queries to both APIs
  - Real-time streaming responses
  - Tool call visibility
  - Error handling and recovery

### 🎯 Comparison: Admin vs Storefront Tools

| Feature | Admin API Tools (9) | Storefront API Tools (2) |
|---------|---------------------|--------------------------|
| **Purpose** | Store management | Customer-facing queries |
| **Authentication** | Admin Access Token | Storefront Access Token |
| **Permissions** | Full access (read/write) | Public read-only |
| **Tool Prefix** | None (default) | `[Storefront]` marker |
| **Example Uses** | Create products, manage orders | Search products, check availability |
| **Agent Guidance** | For management tasks | For customer perspective |

### 🎯 Next Phase: Custom Dashboard with KPI Widgets

**Goal**: Build a visual dashboard featuring real-time Shopify store metrics

**Features to Implement:**
1. **Grid-based dashboard layout** with responsive design
2. **KPI widgets** displaying:
   - 24-hour order value
   - Average Order Value (AOV) - this week vs last week
   - Conversion rate
   - Total orders count
   - Revenue trends
3. **Time-based data comparisons** (current period vs previous period)
4. **Chart visualizations** for sales trends over time
5. **Widget customization** (add, remove, reorder widgets)

**Technical Approach:**
- Use Shopify Admin GraphQL API to fetch order and sales data
- Create reusable KPI widget components
- Implement data aggregation in a DashboardState
- Add chart library for visualizations (recharts or similar)
- Enable real-time data refresh

---

## 📝 Notes

**Phase 1-4.6 Summary:**
- ✅ Removed all non-functional Ollama code
- ✅ Simplified to cloud-only models (Mistral primary, OpenRouter secondary, OpenAI fallback)
- ✅ Enhanced all 9 Shopify Admin API tools with structured, vLLM/vSLM-friendly docstrings
- ✅ Added comprehensive agent instructions with Shopify-specific context
- ✅ Integrated Mistral AI as the primary model provider with native API support
- ✅ **Added full Shopify Storefront API support with separate credentials and testing**
- ✅ **Implemented 2 Storefront API tools with intelligent routing**
- System now supports both Admin and Storefront APIs with intelligent tool selection

**Tool Architecture**:
- **Total Tools**: 11 (9 Admin + 2 Storefront)
- **Admin Tools**: Product (3), Customer (3), Order (3)
- **Storefront Tools**: Product Search & Details (2)
- **Future Expansion**: Collections, Cart operations, Customer accounts

**Next Steps:**
Phase 5 will implement a custom dashboard with KPI widgets showing real-time Shopify store metrics, enabling users to monitor their store performance at a glance.
