# Shopify AI Management App - Refactored Plan

## 🎯 NEW DIRECTION: Cloud-Only AI Models + Enhanced Shopify Tools

**Decision**: Remove Ollama (local model) support entirely. Focus on:
1. Cloud-based AI models (OpenRouter primary, OpenAI fallback)
2. Better encoding Shopify API permissions as vLLM/vSLM-friendly tools
3. Improved tool descriptions and structured outputs

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

**Results**:
- Removed ~25 lines of non-functional Ollama code
- Simplified model selection to cloud-only (OpenRouter → OpenAI)
- Tested successfully: Falls back to OpenAI when OpenRouter key not set
- No more connection errors or misleading logs

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

**Results**:
- Enhanced all 9 Shopify tools with structured docstrings
- Added category tags: [Product Management], [Customer Management], [Order Management]
- Included required Shopify API permissions (read_products, write_products, etc.)
- Added concrete usage examples for each tool
- Full type hints on all parameters
- Tested successfully with Agno agent integration
- All compliance checks passed ✅

**Tool Enhancement Details**:
Each tool now includes:
- **Category Tag**: Helps AI understand tool domain
- **Description**: Clear explanation of functionality
- **Required Permissions**: Shopify API scopes needed
- **Example Usage**: Natural language queries → function calls
- **Type Hints**: Proper Python typing for parameters
- **Return Format**: Structured JSON response description

---

## Phase 3: Improve AI Agent Instructions & Context 🚀 (CURRENT)
**Goal**: Add system prompts and context to help AI understand Shopify operations

### Tasks:
- [ ] Create Shopify-specific system prompt for agent
- [ ] Add context about common Shopify operations
- [ ] Define tool usage patterns and best practices
- [ ] Add examples of complex multi-tool workflows
- [ ] Implement conversation memory with Shopify context
- [ ] Add error recovery patterns for failed API calls

**Status**: 🔜 NEXT

---

## Phase 4: Custom Dashboard with KPI Widgets
**Goal**: Build visual dashboard with real-time Shopify metrics

### Tasks:
- [ ] Design dashboard layout with grid system
- [ ] Implement KPI widgets (24hr order value, AOV, conversion rate)
- [ ] Add time-based comparisons (this week vs last week)
- [ ] Create chart components for sales trends
- [ ] Enable widget customization (add/remove/reorder)

**Status**: ⏳ BACKLOG

---

## Phase 5: PDF Report Generation
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
- Settings page with API key management
- Shopify API integration (9 enhanced tools)
- Chat interface with streaming responses
- Cloud-only model selection (OpenRouter → OpenAI)
- Clean error handling (no more Ollama connection errors)
- vLLM/vSLM-friendly tool descriptions with examples and permissions

### 🎯 What's Next:
**Phase 3**: Add agent context, system prompts, and workflow patterns

---

## 🚀 Ready to Start Phase 3

Add intelligent context and system prompts to help the AI agent better understand and execute Shopify operations.