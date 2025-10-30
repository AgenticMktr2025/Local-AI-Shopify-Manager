# Shopify AI Management App - Enhanced Plan (Make.com Insights Integrated)

## 🎯 VISION: AI-Powered Shopify Store Manager with Make.com-Inspired Automation

**Core Philosophy**: Build an intelligent AI assistant that combines conversational management with automated workflows inspired by Make.com's most powerful Shopify integrations.

**Tech Stack**:
1. Cloud-based AI models (Mistral AI primary, OpenRouter secondary, OpenAI fallback)
2. Shopify Admin + Storefront GraphQL APIs
3. Agno agent framework for tool orchestration
4. Make.com-inspired automation patterns

---

## 🆕 NEW FEATURES INSPIRED BY MAKE.COM

Based on Make.com's Shopify integration templates and automation library, the following capabilities should be added to enhance the AI Store Manager:

### 📦 **Inventory & Product Management**
- **Bulk Product Operations**: Create/update multiple products in batches
- **Inventory Adjustments**: Adjust inventory levels with reason tracking
- **Product Variants**: Full variant management (create, update, delete)
- **Collections Management**: Create and manage product collections
- **Metafields**: Read/write custom metafields for products, customers, orders
- **Tags Management**: Automated tagging based on rules or AI suggestions

### 💰 **Pricing & Promotions**
- **Discount Code Management**: Create, update, list discount codes
- **Price Rules**: Automated pricing adjustments based on conditions
- **Gift Card Operations**: Create and manage gift cards
- **Price Monitoring**: Track price changes and competitor analysis

### 📧 **Customer Engagement**
- **Email Notifications**: Automated customer emails for order status, inventory restocks
- **Customer Segmentation**: Tag-based customer grouping for targeted campaigns
- **Loyalty & Rewards**: Track customer lifetime value, implement reward programs
- **Review Management**: Collect and respond to product reviews

### 📊 **Order Processing & Fulfillment**
- **Fulfillment Workflows**: Create fulfillments, assign to locations
- **Refund Processing**: Issue refunds with reason tracking
- **Order Tagging**: Automated order classification and prioritization
- **Shipping Label Generation**: Integration with shipping providers
- **Returns Management**: Handle returns and exchanges

### 🔔 **Webhooks & Event Management**
- **Real-time Webhooks**: Subscribe to Shopify events (new orders, inventory changes, etc.)
- **Event-Driven Automation**: Trigger actions based on store events
- **Custom Notifications**: Slack/email alerts for critical events

### 📈 **Analytics & Reporting**
- **Sales Analytics**: Revenue trends, best-selling products, AOV tracking
- **Customer Analytics**: Customer acquisition, retention, lifetime value
- **Inventory Reports**: Stock levels, low inventory alerts, turnover rates
- **Custom Reports**: Export data as CSV/PDF with custom date ranges
- **Predictive Analytics**: AI-powered sales forecasting and demand prediction

### 🤖 **AI-Enhanced Features**
- **Product Description Generator**: AI-generated SEO-optimized product descriptions
- **Smart Tagging**: AI-suggested tags and collections for products
- **Customer Inquiry Assistant**: AI responses to common customer questions
- **Inventory Forecasting**: Predict stock needs based on historical data
- **Pricing Optimization**: AI recommendations for optimal pricing

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

---

## Phase 5: Expand Admin API Tools (Make.com Inspired) ✅
**Goal**: Add critical Shopify Admin tools inspired by Make.com's most-used automation templates

### 5A: Product & Inventory Tools ✅
- [x] **Create Product Variant**: Add variants to existing products
- [x] **Update Product Variant**: Modify variant properties (SKU, price, inventory)
- [x] **Delete Product Variant**: Remove variants from products
- [x] **Adjust Inventory Level**: Update stock quantities with reason tracking
- [x] **Get Inventory Levels**: Query inventory across multiple locations
- [x] **Create Collection**: Create smart or manual collections
- [x] **Add Products to Collection**: Bulk add products to collections
- [x] **Get Product Metafields**: Read custom product metadata
- [x] **Set Product Metafield**: Write/update custom metafields

**Status**: ✅ COMPLETE

### 5B: Order & Fulfillment Tools ✅
- [x] **Create Fulfillment**: Mark orders as fulfilled with tracking info
- [x] **Get Fulfillment Orders**: Retrieve fulfillment details
- [x] **Cancel Order**: Cancel unfulfilled orders
- [x] **Create Refund**: Issue full or partial refunds
- [x] **Add Order Note**: Add internal notes to orders
- [x] **Tag Order**: Apply tags for order classification
- [x] **Update Fulfillment Tracking**: Update shipping status

**Status**: ✅ COMPLETE

### 5C: Customer & Engagement Tools ✅
- [x] **Tag Customer**: Apply tags for segmentation
- [x] **Remove Customer Tags**: Clean up customer tags
- [x] **Get Customer Metafields**: Retrieve custom customer data
- [x] **Set Customer Metafield**: Store loyalty points, preferences, etc.
- [x] **Search Orders by Customer Email**: Quick customer order lookup

**Status**: ✅ COMPLETE

### 5D: Pricing & Promotions Tools
- [ ] **Create Discount Code**: Generate promo codes programmatically
- [ ] **List Discount Codes**: View all active discount codes
- [ ] **Update Discount Code**: Modify discount rules and expiry
- [ ] **Delete Discount Code**: Remove expired or invalid codes
- [ ] **Create Gift Card**: Generate gift cards with custom amounts

**Status**: ⏳ NEXT UP

---

## Phase 6: Event-Driven Automation (Webhook System) 
**Goal**: Implement real-time event monitoring and automated workflows

### Tasks:
- [ ] Design webhook management system for Shopify events
- [ ] Create webhook subscription tools (new orders, inventory changes, etc.)
- [ ] Implement event listener service for real-time notifications
- [ ] Add Slack/email notification integration for critical events
- [ ] Build rule-based automation engine (if X happens, do Y)
- [ ] Create UI for managing automation rules
- [ ] Add webhook testing and debugging tools

**Status**: ⏳ BACKLOG

---

## Phase 7: Advanced Analytics Dashboard
**Goal**: Build comprehensive analytics and reporting system

### 7A: Sales Analytics
- [ ] Revenue trends (daily, weekly, monthly)
- [ ] Best-selling products dashboard
- [ ] Average Order Value (AOV) tracking
- [ ] Conversion rate monitoring
- [ ] Sales by traffic source

### 7B: Customer Analytics
- [ ] Customer lifetime value (CLV) calculation
- [ ] Customer acquisition cost (CAC) tracking
- [ ] Retention rate metrics
- [ ] Customer segmentation visualization
- [ ] Churn prediction

### 7C: Inventory Analytics
- [ ] Stock level monitoring with low inventory alerts
- [ ] Inventory turnover rates
- [ ] Product velocity tracking
- [ ] Reorder point recommendations
- [ ] Dead stock identification

### 7D: Reporting Features
- [ ] Custom date range selection
- [ ] Export reports as CSV/PDF
- [ ] Scheduled report generation
- [ ] Email report delivery
- [ ] Custom KPI widget builder

**Status**: ⏳ BACKLOG

---

## Phase 8: AI-Enhanced Features
**Goal**: Leverage AI for intelligent store management

### Tasks:
- [ ] **Product Description Generator**: AI-generated SEO product descriptions
- [ ] **Smart Tagging System**: AI-suggested tags for products/orders/customers
- [ ] **Inventory Forecasting**: Predict stock needs using historical data
- [ ] **Pricing Optimization**: AI recommendations for competitive pricing
- [ ] **Customer Support Assistant**: AI-powered responses to common queries
- [ ] **Sentiment Analysis**: Analyze customer reviews and feedback
- [ ] **Fraud Detection**: AI-based suspicious order flagging

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
  - **30 Admin API tools** for management operations (Product/Inventory/Customer/Order/Fulfillment)
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

### 🎯 Tool Inventory

| Category | Admin API Tools | Storefront API Tools |
|----------|----------------|----------------------|
| **Products** | 10 (get, get-by-id, create, variants, collections, metafields) | 2 (search, get-by-handle) |
| **Inventory** | 2 (get-levels, adjust) | - |
| **Customers** | 8 (get, update, get-orders, tag, remove-tags, metafields, search-orders) | - |
| **Orders** | 3 (get, get-by-id, update) | - |
| **Fulfillment** | 7 (create, get, cancel, refund, note, tag, tracking) | - |
| **Total** | **30 tools** | **2 tools** |

### 🚀 Make.com Integration Priorities

Based on Make.com's most popular Shopify templates, these features should be prioritized:

**HIGH PRIORITY** (Phase 5):
1. ✅ Product Variants (create, update, delete)
2. ✅ Inventory Management (adjust levels, track across locations)
3. ✅ Fulfillment Operations (create fulfillments, update tracking)
4. ✅ Refund Processing (issue refunds with reasons)
5. ⏳ Discount Code Management (create, list, update, delete)
6. ✅ Collections Management (create, add products)
7. ✅ Metafields (product, customer, order metadata)
8. ✅ Customer Tagging & Segmentation

**MEDIUM PRIORITY** (Phase 6):
1. Webhook Subscriptions (real-time event monitoring)
2. Order Tagging (automated classification) - ✅ Basic tagging complete
3. Customer Segmentation (tag-based grouping) - ✅ Complete
4. Email Notifications (automated customer communications)

**FUTURE ENHANCEMENTS** (Phases 7-8):
1. Analytics Dashboard (sales, inventory, customer metrics)
2. AI-Generated Content (product descriptions, tags)
3. Predictive Analytics (inventory forecasting, demand prediction)
4. Pricing Optimization (AI-powered price recommendations)

---

## 📝 Implementation Notes

**Phase 1-5C Summary:**
- ✅ Removed all non-functional Ollama code
- ✅ Simplified to cloud-only models (Mistral primary, OpenRouter secondary, OpenAI fallback)
- ✅ Enhanced all Shopify Admin API tools with structured, vLLM/vSLM-friendly docstrings
- ✅ Added comprehensive agent instructions with Shopify-specific context
- ✅ Integrated Mistral AI as the primary model provider with native API support
- ✅ Added full Shopify Storefront API support with separate credentials and testing
- ✅ Implemented 2 Storefront API tools with intelligent routing
- ✅ **Expanded Admin API to 30 tools with Phase 5A, 5B & 5C complete**

**Phase 5A Achievements:**
- ✅ **9 new tools added**: Product variants (create/update/delete), Inventory management (get levels/adjust), Collections (create/add products), Metafields (get/set)
- ✅ **Tool count increased from 9 to 18** - 100% growth in Admin API capabilities
- ✅ All tools follow Make.com-inspired patterns for automation readiness
- ✅ Comprehensive docstrings with [Category] prefixes and usage examples
- ✅ GraphQL-based implementation with proper error handling
- ✅ Permission requirements documented for each tool

**Phase 5B Achievements:**
- ✅ **7 new tools added**: Fulfillment operations (create/get/update tracking), Order management (cancel/refund/note/tag)
- ✅ **Tool count increased from 18 to 25** - 39% growth with critical order processing capabilities
- ✅ Complete fulfillment workflow support with tracking integration
- ✅ Comprehensive refund and cancellation functionality
- ✅ Order tagging and note management for internal tracking
- ✅ All tools have detailed docstrings with real-world usage examples
- ✅ Proper error handling and session management

**Phase 5C Achievements:**
- ✅ **5 new tools added**: Customer engagement (tag/remove tags), Customer metafields (get/set), Order search by email
- ✅ **Tool count increased from 25 to 30** - 20% growth with advanced customer management
- ✅ Complete customer segmentation support with tagging capabilities
- ✅ Custom customer data storage via metafields (loyalty points, preferences)
- ✅ Quick order lookup by customer email for support workflows
- ✅ All tools have [Customer Management] or [Order Management] category prefixes
- ✅ Comprehensive docstrings with real-world usage scenarios

**Make.com Integration Insights:**
- Make.com's Shopify integration offers 20+ actions, 5+ triggers, and custom GraphQL/REST API calls
- Most popular automations: Inventory sync, order notifications, customer segmentation, discount management
- Key workflow patterns: Event-driven (webhooks) + scheduled (batch operations) + manual (on-demand)
- Critical features for AI Store Manager: Variants, inventory, fulfillments, refunds, discounts, metafields

**Next Phase:**
Phase 5D will add 5 Pricing & Promotions tools (discount codes: create/list/update/delete, gift cards). This will complete the core Make.com-inspired automation foundation with 35+ Admin API tools total.