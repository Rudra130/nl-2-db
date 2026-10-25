# Claymorphism Design System Specification (`NL2DB` Frontend)

> **Note**: This file is identical to [claf-design.README.md](file:///c:/Users/rudra/OneDrive/Desktop/db%20language/claf-design.README.md).

## 1. Executive Summary & Design Vision

**Claymorphism** is a modern 3D UI aesthetic that builds upon the softness of neumorphism and the vibrancy of flat/glass design. Unlike glassmorphism (which focuses on backdrop blurs, translucency, and glass borders), **Claymorphism introduces inflated, tactile, matte 3D surfaces** reminiscent of clay or soft rubber models.

This specification details how we will incorporate Claymorphism into the **NL2DB (Natural Language to Database)** web frontend across both **Dark Mode** and **Light Mode**, creating a playful, tactile, and state-of-the-art interactive query platform.

---

## 2. Core Anatomical Principles of Claymorphism

Claymorphism relies on **four core CSS building blocks**:

1. **Large Corner Radii**:
   - Panels, cards, and inputs feature heavy rounding (`16px`, `20px`, `24px`, or `pill/full`).
2. **Dual Inset Shadows (3D Volume & Depth)**:
   - **Top-Left Inset Highlight**: Simulates a light source striking the top edge of the clay object.
   - **Bottom-Right Inset Shadow**: Simulates the internal contour and curved depth.
   - *Formula*: 
     ```css
     box-shadow: 
       /* Outer elevated shadow */
       0 12px 24px -6px var(--clay-shadow-outer),
       0 4px 8px -2px var(--clay-shadow-outer-sm),
       /* Inner bevel light reflection */
       inset 3px 3px 6px var(--clay-inset-light),
       /* Inner contour depth */
       inset -4px -4px 8px var(--clay-inset-dark);
     ```
3. **Tactile Matte Backgrounds**:
   - Instead of transparent glass reflections, claymorphism uses solid or softly gradient-filled matte surfaces.
4. **Squishy Micro-Interactions**:
   - **Resting state**: Floating with depth (`translateY(0)`).
   - **Hover state**: Floats up slightly (`transform: translateY(-3px) scale(1.008)`), shadow expands.
   - **Active/Pressed state**: Tactile "clay squish" depression (`transform: translateY(2px) scale(0.99)`), inset shadows deepen.

---

## 3. Light & Dark Clay Design System

### 3.1 Light Mode Clay Tokens
- **Background**: Soft chalk/cloud background (`#edf2f7`).
- **Clay Card Fill**: Clean soft clay (`#f8fafc` or subtle warm white).
- **Clay Inset Light**: Solid pure white highlight (`rgba(255, 255, 255, 0.9)`).
- **Clay Inset Dark**: Soft slate curvature (`rgba(148, 163, 184, 0.45)`).
- **Clay Outer Drop Shadow**: Warm diffuse shadow (`rgba(100, 116, 139, 0.25)`).
- **Clay Primary Button**: Violet-Indigo clay (`#7c3aed`) with pure white top-left highlight and deep indigo inner contour.
- **Clay Secondary Button**: Tactile pill with subtle dual insets.

### 3.2 Dark Mode Clay ("Obsidian Clay") Tokens
- **Background**: Deep void slate (`#090d16`).
- **Clay Card Fill**: Obsidian matte finish (`#121826`).
- **Clay Inset Light**: Glowing neon violet/cyan rim highlight (`rgba(255, 255, 255, 0.12)` or `rgba(139, 92, 246, 0.2)`).
- **Clay Inset Dark**: Deep void depression (`rgba(0, 0, 0, 0.7)`).
- **Clay Outer Drop Shadow**: Deep ambient shadow (`rgba(0, 0, 0, 0.6)`).
- **Clay Primary Button**: Luminous purple clay with vibrant inner glow.

---

## 4. Component Transformation Plan

### Component 1: `Header.jsx`
- Floating clay bar with rounded bottom corners (`20px`) and subtle outer lift.
- Clay brand icon: 3D embossed logo button with deep inset shadows.
- DB Selector & Ping Button: Molded tactile clay selector pills.
- Sun/Moon Theme Toggle: A molded 3D toggle switch with tactile click depression.

### Component 2: `SchemaExplorer.jsx`
- Molded sidebar panel with dual insets.
- Search input: Inset clay carved into the panel (`inset 2px 2px 5px ...`).
- Table items: Raised clay blocks that smoothly depress when expanded.
- Column pills & badges: Soft molded clay badges with custom database color insets.

### Component 3: `QueryInput.jsx`
- Query container: Elevated clay panel.
- Natural Language Textarea: Carved inner clay well (looks carved into the clay body).
- Example pills: Bouncy 3D clay bubbles that lift on hover and depress on click.
- "Run Query" Button: Chunky, high-tactility 3D clay action button with glowing inner bevels.

### Component 4: `SummaryCard.jsx`
- Sculpted executive clay card with subtle purple-tinted matte body.
- Metric chips (Rows, Latency): Molded mini-clay indicators.
- Business insights: Nested 3D clay tiles with soft green/purple check icons.

### Component 5: `ResultTable.jsx`
- Container: Softly rounded elevated clay slab (`24px` radius).
- Search & Export controls: Sculpted tactile clay buttons and carved search bar.
- Data table: Smooth, curved headers and rounded table rows with soft clay hover states.

### Component 6: `QueryInspector.jsx` & `ErrorBanner.jsx`
- Modal dialog: Deeply elevated 3D clay dialog with floating backdrop.
- Code block: Carved matte obsidian block with indented bezel.
- Error banner: Tactile amber/crimson clay alert cushion with embossed warning shield.

---

## 5. Implementation Phases

1. **Phase 1: Design Tokens & CSS Architecture**
   - Add Claymorphism CSS custom properties to `frontend/src/index.css` for both `[data-theme="dark"]` and `[data-theme="light"]`.
   - Implement `.clay-card`, `.clay-btn`, `.clay-input`, `.clay-inset`, and `.clay-badge` utility classes.

2. **Phase 2: Header & Navigation Clay Polish**
   - Style the header bar, connection selector, theme toggle, and status indicators with claymorphic elevation.

3. **Phase 3: Query & Input Components**
   - Upgrade `QueryInput.jsx` with carved prompt box, clay pills, and 3D action button.
   - Refactor `SchemaExplorer.jsx` with carved search and tactile table accordions.

4. **Phase 4: Results, Summary & Inspection**
   - Style `SummaryCard.jsx`, `ResultTable.jsx`, `QueryInspector.jsx`, and `ErrorBanner.jsx` with clay elevations and micro-interactions.

5. **Phase 5: Verification & Quality Assurance**
   - Run production bundle build (`npm run build`).
   - Validate visual aesthetics across dark and light modes.
