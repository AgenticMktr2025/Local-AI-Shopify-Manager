# Shopify AI Management App - Refactored Plan

## 🎯 NEW DIRECTION: Cloud-Only AI Models + Enhanced Shopify Tools

**Decision**: Remove Ollama (local model) support entirely. Focus on:
1. Cloud-based AI models (Mistral AI primary, OpenRouter secondary, OpenAI fallback)
2. Better encoding Shopify API permissions as vLLM/vSLM-friendly tools
3. Improved tool descriptions and structured outputs
4. Intelligent agent instructions and context

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
- Settings page with API key management (Shopify, Mistral, OpenRouter, OpenAI)
- Shopify API integration (9 enhanced tools with vLLM/vSLM-friendly descriptions)
- Chat interface with streaming responses
- Cloud-only model selection with intelligent fallback: Mistral → OpenRouter → OpenAI
- Clean error handling and model availability detection
- Intelligent agent instructions with Shopify-specific context
- Native Mistral AI Studio integration for cost-effective, high-performance AI

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
- Use Shopify GraphQL API to fetch order and sales data
- Create reusable KPI widget components
- Implement data aggregation in a DashboardState
- Add chart library for visualizations (recharts or similar)
- Enable real-time data refresh

---

## 📝 Notes

**Phase 1-4 Summary:**
- ✅ Removed all non-functional Ollama code
- ✅ Simplified to cloud-only models (Mistral primary, OpenRouter secondary, OpenAI fallback)
- ✅ Enhanced all 9 Shopify tools with structured, vLLM/vSLM-friendly docstrings
- ✅ Added comprehensive agent instructions with Shopify-specific context
- ✅ Integrated Mistral AI as the primary model provider with native API support
- System is now ready for advanced features like custom dashboards and analytics

**Next Steps:**
Phase 5 will implement a custom dashboard with KPI widgets showing real-time Shopify store metrics, enabling users to monitor their store performance at a glance.