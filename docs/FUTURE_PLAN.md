# 🔮 Future Development Plan

This document outlines planned architectural improvements for Nano Papl.

> [!IMPORTANT]
> **Document Rules:**
> - **Never delete entries** — only update their status when resolved
> - Move completed items to the `📜 Completed` section at the bottom
> - Add completion date and version (e.g., `Resolved: v1.3.1, 2026-01-18`)
> - This file serves as the **single source of truth** for all tasks, bugs, and improvements

**Status Legend:**
| Status | Meaning |
|--------|---------|
| 🔴 To Fix | High priority bug, blocking |
| 🟡 Planned | Approved for implementation |
| 🔵 In Progress | Currently being worked on |
| ⚪ Backlog | Low priority, future consideration |
| 🟢 Completed | Done, moved to Completed section |



## Plugin Architecture for Tools

**Status:** Planned  
**Priority:** Medium (when pages exceed 7-8)

### Current State
Pages are manually registered in `ui/window.py`:
```python
self.batch_interface = BatchPage(self.config_manager, self)
self.addSubInterface(self.batch_interface, FluentIcon.PROJECTOR, "Generation")
```

### Problem
As the number of tools grows, `window.py` becomes cluttered with imports and registrations.

### Proposed Solution
Create a registry-based plugin system:

```python
# ui/pages/__init__.py
PAGES = [
    ("batch_page", "BatchPage", FluentIcon.PROJECTOR, "Generation"),
    ("chat_page", "ChatInterface", FluentIcon.CHAT, "Chat"),
    ("constructor_page", "ConstructorPage", FluentIcon.TILES, "Prompts Builder"),
    # New tools just add a line here
]

# ui/window.py
import importlib
from ui.pages import PAGES

for module_name, class_name, icon, title in PAGES:
    module = importlib.import_module(f"ui.pages.{module_name}")
    PageClass = getattr(module, class_name)
    page = PageClass(self.config_manager, self)
    self.addSubInterface(page, icon, title)
```

### Benefits
- Zero changes to `window.py` when adding new tools
- Clear separation of concerns
- Easy to enable/disable tools via configuration

### Implementation Trigger
Implement when total page count exceeds 7-8.

---

## UI Standardization (Technical Debt)

**Status:** Planned  
**Priority:** Low (cosmetic, not functional)

### Current State
Some UI components use manual implementations instead of native QFluentWidgets equivalents:
- `QLabel` instead of `TitleLabel`/`BodyLabel`/`CaptionLabel`
- `QFont` manual sizing instead of Fluent typography
- Hardcoded hex colors (`#ffffff`) instead of `UIConfig` constants
- Inline `setStyleSheet()` instead of `ThemeAwareBackground` pattern
- `QPushButton` instead of `PrimaryPushButton`/`TransparentPushButton`

### Problem
This leads to:
1. **Inconsistent theming** — some elements don't react to theme changes
2. **Scattered style definitions** — colors defined in multiple files
3. **Harder maintenance** — changes require hunting through codebase
4. **Visual inconsistencies** — subtle differences in spacing/fonts

### Proposed Solution
1. **Migrate all labels** → Use `TitleLabel`, `BodyLabel`, `CaptionLabel`, `SubtitleLabel`
2. **Centralize colors** → All hex codes in `UIConfig` only
3. **Use Fluent buttons** → Replace `QPushButton` with Fluent equivalents
4. **Theme subscription** → All custom widgets connect to `qconfig.themeChanged`

### Affected Files
- `ui/widgets/chat/` — bubble colors, input area
- `ui/widgets/batch/` — preview panel, status labels
- `ui/components.py` — base components
- `ui/pages/` — various pages

### Implementation Trigger
Perform during next major UI feature addition or refactor.

---

## Vertex AI Provider Integration

**Status:** ⚪ Backlog  
**Priority:** Medium  
**Estimated Effort:** ~2-3 hours

### Current State
The app uses **Google AI Studio** (free/pay-as-you-go API key) with `google.genai` SDK. Only two models available:
- `gemini-3-pro-image-preview` — text + image generation
- `gemini-3-flash-preview` — text only

### What Vertex AI Offers
Vertex AI is Google Cloud's enterprise ML platform. Key differences:

| Feature | AI Studio (Current) | Vertex AI |
|---------|--------------------|-----------|
| Auth | API Key | GCP Service Account / ADC |
| Models | 2 Gemini models | All Gemini + Imagen 3/4, Claude via Model Garden, Llama, etc. |
| Rate Limits | 15 RPM (free), 1000+ RPM (paid) | Configurable per-project quotas |
| Pricing | Per-token/image | Same rates, but GCP billing |
| Image Gen | Gemini native only | Imagen 3/4 (higher quality, more styles) |
| Region | Global | Region-specific endpoints |

### Feasibility Analysis

**Good news:** The existing architecture is perfectly ready. `LLMProviderFactory` already uses a Factory pattern:
```
LLMClient → LLMProviderFactory.get_provider("gemini") → GeminiProvider
                                           ("vertex") → VertexAIProvider  ← NEW
```

The `google.genai` SDK (`google-genai` package) **already supports Vertex AI** natively. The only difference is initialization:
```python
# Current (AI Studio)
client = genai.Client(api_key="...")

# Vertex AI — same SDK, different auth
client = genai.Client(
    vertexai=True,
    project="my-gcp-project",
    location="us-central1"
)
```

After this single change, **all `client.models.generate_content()` and `client.chats.create()` calls remain identical.** Zero changes to the generation logic.

### Implementation Steps
1. Add a Settings toggle: "Use Vertex AI" with fields for GCP Project ID and Region
2. Create `VertexAIProvider(LLMProvider)` in `llm_factory.py` — mostly a copy of `GeminiProvider` with different `Client()` init
3. Update `LLMProviderFactory` to route to the correct provider
4. Add `google-auth` dependency for ADC (Application Default Credentials)
5. Optionally: add Imagen model support as a separate generation mode

### Is It Worth It?

**Yes, if:**
- You want access to **Imagen 3/4** (much better at photorealistic generation than Gemini native)
- You need higher rate limits for production use
- You want to test new models as Google releases them (Model Garden)

**Not worth it if:**
- You're happy with current Gemini image generation quality
- Setting up GCP billing and service accounts feels like overhead
- The free tier is sufficient for your usage

### Conclusion
Thanks to the existing Factory pattern, this is a **low-effort, high-value** addition. The SDK is the same (`google-genai`), so the change is mostly about authentication and adding a UI toggle. The biggest unlock is access to **Imagen** and **higher rate limits**.

---

## Parallel Chat Generation Queue

**Status:** ⚪ Backlog  
**Priority:** Low (nice-to-have)

### Current State
Chat generation is strictly sequential — the user must wait for each request to complete before sending the next one.

### Problem
When generating multiple 4K images in chat, the user has to wait 30-60s per image. Queuing 10 prompts and letting them process in parallel would dramatically improve throughput.

### Proposed Solution
Google Gemini API allows concurrent requests on a single API key (limited by RPM/RPD). Implementation would require:
1. Replace single `self.worker` with a worker pool or `asyncio`-based queue
2. Allow submitting multiple prompts while previous ones are still processing
3. Results arrive and display in chat as they complete
4. Respect RPM limits (15 req/min on free tier)

### Benefits
- Much faster workflow for bulk image generation in chat
- No need to wait for each individual response

### Implementation Trigger
Implement when chat-based image generation becomes the primary workflow.

---

## 📜 Completed

### � BUG: Taskbar Icon Not Displayed on First Launch

**Resolved:** v1.3.1, 2026-01-20
**Original Priority:** Medium

**Problem:** The application icon does not appear in the Windows taskbar on the first launch. It only appears after restarting the application.

**Fix Applied:**
1. Updated `main.py` to use `ResourceManager.get_asset()` for retrieving the absolute path of the icon file.
2. Replaced the relative path `"assets/ico.ico"` with the absolute path resolved at runtime.

**Files Changed:** `main.py`

### 🟢 BUG: RPD Counter Not Working

**Resolved:** v1.3.1, 2026-01-20
**Original Priority:** Medium

**Problem:** The Rate Per Day counter always showed 13 regardless of actual usage. The counter should reset each calendar day. Label was also typo'd as "RDP".

**Fix Applied:** 
1. Renamed "RDP" to "RPD" in UI labels.
2. Refined `check_api_usage` and `increment_api_usage` in `batch_page.py` to be robust against missing or corrupted config data.
3. Verified daily reset logic with standalone script.

**Files Changed:** `ui/pages/batch_page.py`, `ui/widgets/batch/config_panel.py`

### 🟢 BUG: Chat Deletion Creates Infinite "New Chat" Loop

**Resolved:** 2026-01-18  
**Original Priority:** High

**Problem:** When deleting a chat, a new "New Chat" was created instead. These chats couldn't be deleted, causing infinite loop.

**Root Cause:** `delete_session()` called `start_new_chat()` which called `_refresh_sidebar()`, then `delete_session()` called `_refresh_sidebar()` again.

**Fix Applied:**
1. `delete_session()` now clears state first, then refreshes sidebar, then selects existing session or creates new as fallback
2. Added `refresh_sidebar` flag to `start_new_chat()` to skip refresh when called as fallback

### 🟢 PERFORMANCE: RPD Counter Lag Optimization

**Resolved:** v2.0.0, 2026-01-21
**Original Priority:** Critical

**Problem:** Generation was extremely slow because the app saved the entire config file to disk after every single image to update the daily counter.

**Fix Applied:**
1. Optimized `BatchPage` to update the counter in memory during batch processing.
2. Saving to disk now only happens when the batch finishes or is stopped.

**Files Changed:** `ui/pages/batch_page.py`

### 🟢 BUG: Google API Hanging (504 Timeout)

**Resolved:** v2.0.0, 2026-01-21
**Original Priority:** Critical

**Problem:** The application would hang indefinitely or fail with `504 DEADLINE_EXCEEDED` because the new Google GenAI SDK lacks a default timeout, and the server was taking longer than expected.

**Fix Applied:**
1. Added explicit `http_options={'timeout': 600000}` (10 minutes) to the generation config.
2. Added detailed logging to track request duration.

**Files Changed:** `core/services/generation_service.py`

### 🟢 UX: API Key Visibility

**Resolved:** v2.0.0, 2026-01-21
**Original Priority:** Low

**Problem:** Users couldn't verify if their API Key was entered correctly because it was masked as a password.

**Fix Applied:**
1. Changed `EchoMode` of the API Key input field from Password to Normal.

**Files Changed:** `ui/pages/settings_page.py`

### 🟢 UX: Configurable API Timeout

**Resolved:** v2.0.0, 2026-01-21
**Original Priority:** Medium

**Problem:** Users couldn't maximize the window properly because the orange state tooltip was not anchored. Also, the API timeout was hardcoded, causing issues with slow connections/models.

**Fix Applied:**
1. Added `resizeEvent` to `NPBasePage` to keep tooltips anchored.
2. Added `api_timeout` field to `SettingsPage` (SpinBox) with a default of 600s.

**Files Changed:** `ui/components.py`, `ui/pages/settings_page.py`, `core/models.py`

### 🟢 UX: Secure API Key Toggle

**Resolved:** v2.0.0, 2026-01-21
**Original Priority:** Low

**Problem:** API Key was either always hidden (bad for verification) or always visible (bad for security).

**Fix Applied:**
1. Implemented a "Show/Hide" toggle button (Eye icon) next to the API Key field.
2. Default state is hidden (Password mode), user clicks to reveal.

**Files Changed:** `ui/pages/settings_page.py`
