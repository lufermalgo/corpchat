# Figma Make — Apply Brand Background Pattern to All Slides (exclude Cover/Contact)

**Goal**  
Recreate and apply the attached brand background pattern to every slide **except** Cover/Portada and Contact/Contacto. The pattern must be full‑bleed, non‑intrusive for text, and consistent with the deck’s 16:9 canvas and SafeArea (64 px).

> This is a **visual-only background**; content continues to live in `Content` (SafeArea). Do **not** modify TitleBar, ContentBody, or Masters.

---

## 0) Constants
- Canvas: **1920×1080** (16:9).
- SafeArea (content): **64 px** margin on all sides (already present in `Content`).
- Brand variables (use variables, no raw hex):
  - `color/primary = #96BD1C` (green)
  - `color/accent  = #F0E308` (yellow)
  - `neutral/bg    = #FFFFFF`
  - `neutral/fg    = #0F110B`

---

## 1) Create Background Component `BG/BrandPattern`
Create a **component** (not frame) named **`BG/BrandPattern`**, sized **1920×1080**, with the following **layers (bottom → top)**. All shapes **must extend beyond canvas edges** to avoid hairlines when exporting.

1. **Base Layer (`BG/Base`)**
   - Rectangle 1920×1080.
   - **Fill**: `neutral/bg` (white).

2. **Left Gradient Bar (`BG/LeftBar`)**
   - Rectangle aligned to **left edge**, width **96 px** (≈5% of width), height **100%**.
   - Fill: **linear gradient** top→bottom using brand greens:  
     - Stop 0%: `color/primary @100%`  
     - Stop 100%: `color/primary @70%`  
   - No stroke. Soft **inner shadow** optional: y:2, blur:10, opacity:10% to add depth.

3. **Bottom‑Left Bevel Arc (`BG/BevelArc`)**
   - Large circle (oval) positioned so that only a **quarter arc** appears at bottom‑left.  
   - **Radius**: **320 px** (diameter 640). Place center at **(0,1080)** so the arc enters from bottom‑left.
   - Fill: `neutral/bg` (white).  
   - **Drop shadow**: y:4, blur:24, opacity:12% to create a subtle emboss effect.

4. **Top‑Right Circle Stack (`BG/TopRight`)**
   - **Large circle (yellow)**: radius **160 px** (diameter 320). Position so that ~**30%** of the circle sits outside the canvas at top‑right (x:1920−160, y:−96).
     - Fill: `color/accent` (yellow).  
     - **Outer stroke**: 8 px in white (`neutral/bg`) to create the ring.  
     - **Shadow**: y:6, blur:24, opacity:10% (soft).
   - **Small circle (green)**: radius **72 px** (diameter 144). Position partially overlapping the large yellow at its lower‑left quadrant (approx. anchor at x: 1920−240, y: 88).
     - Fill: `color/primary`.  
     - Shadow: y:4, blur:16, opacity:10%.

5. **Optional Soft Vignette (`BG/Vignette`)**
   - Radial gradient covering the canvas, center ~**(400,540)**, to subtly draw eye to center.  
   - Colors: inner `#000000 @0%` → outer `#000000 @4–6%`.  
   - Set **blend mode**: Multiply; **opacity 6%** max.
   - This layer is **disabled** by default in “Light” variant (see §2).

> **Constraints for all layers**: `Left+Right+Top+Bottom` (Fill container). Lock the component after creation.

---

## 2) Variants (accessibility)
Add two variants to `BG/BrandPattern`:
- **`Light`** (default): as described above; `BG/Vignette` hidden.
- **`HighContrast`**: enable `BG/Vignette` and increase left‑bar gradient contrast (`primary @100%` → `primary @60%`). Use when background images or very light content require extra separation.

---

## 3) Apply to Slides (bulk)
For every slide whose name **does not** match `(Cover|Portada|Contact|Contacto)` (case‑insensitive):

1. Ensure the slide’s root frame `Slide/*` has a bottom rectangle named `BG` or a background container.  
2. **Replace** that layer with an **instance** of `BG/BrandPattern/Light`.  
   - Position: **0,0**; size **1920×1080**; **constraints Fill container**.  
   - Send to **back**; **Lock** the instance.  
3. If the slide has busy content or low contrast, switch the instance to the **HighContrast** variant.

**Important**: Do **not** change `Header`, `Footer`, or `Content` structure. The background sits **behind** everything.

---

## 4) SafeArea & Title Protection
- Keep `Content` padding **64 px** so that the TitleBar always sits at **Y=64** from inner top.  
- Ensure no part of the top‑right circle overlaps the TitleBar text area: if it does in a specific slide, slightly nudge `BG/TopRight` group **10–24 px** outward (use overrides on the instance), keeping at least **24 px** clearance from the Title baseline.

---

## 5) Export & Performance
- Convert the component to **vector shapes** (no embedded rasters).  
- Use **paint styles** for gradients so color updates propagate.  
- Keep total background component size **< 100 KB**. Avoid excessive blur radii.  
- When exporting slides, keep text vectors and export **PDF 1920×1080 RGB**.

---

## 6) QA — Background Pattern
Create/update page **`_QA — Brand Background`** listing per slide:
```
{slideName, bgInstance (Light/HighContrast), leftBarW==96?, topRightClearance>=24?, contrastAA (OK/Fail), locked (Yes/No)}
```
Flag **Fail** where the Title area has <24 px clearance or AA contrast fails; suggest switching to `HighContrast` variant.

---

## 7) Safeguards
- Do **not** apply to slides named `(Cover|Portada|Contact|Contacto)`.  
- Do **not** detach the `BG/BrandPattern` instance.  
- Do **not** alter TitleBar/ContentBody; this is a **background‑only** change.
