# UI/UX Design System - Consulting Jobs Dashboard

## 🎨 Design Overview

Complete redesign based on Y Combinator's design language with a premium, minimalist aesthetic.

---

## 🌈 Color Scheme

| Color | Value | Usage |
|-------|-------|-------|
| **Primary** | `#8A8575` | Headings, accents, badges |
| **Accent** | `#2299DD` | Links, location badges, highlights |
| **Background** | `#F5F5EE` | Page background |
| **Surface** | `#FFFFFF` | Cards, headers, content areas |
| **Text Primary** | `#16140F` | Main text, headings |
| **Text Secondary** | `#5C5952` | Secondary text |
| **Text Muted** | `#8A8575` | Tertiary text, labels |
| **Link** | `#2299DD` | All links |
| **Black** | `#000000` | Primary buttons, strong accents |

---

## 📝 Typography

### Fonts

**Headings:** Outfit
- Weights: 300, 400, 500, 600, 700
- Usage: Headers, buttons, labels, UI elements

**Body:** Source Serif 4
- Weights: 300, 400, 500, 600
- Usage: Paragraphs, descriptions, long-form text

### Font Sizes

```css
H1: 24px (heading font)
H2: 20px (heading font)
H3: 18px (heading font)
H4: 16px (heading font)
Body: 14px (serif font)
Small: 13px (heading font)
XS: 12px (heading font)
```

---

## 📐 Spacing System

Base unit: **8px**

```
--spacing-1: 8px
--spacing-2: 16px
--spacing-3: 24px
--spacing-4: 32px
--spacing-5: 40px
--spacing-6: 48px
--spacing-8: 64px
```

---

## 🔲 Border Radius

```
--radius-none: 0px (sharp corners - primary style)
--radius-sm: 4px
--radius-md: 8px
--radius-lg: 12px
--radius-xl: 16px
--radius-full: 9999px (pills, circles)
```

**Design Principle:** Sharp, architectural corners for cards and containers. Rounded pills for buttons and badges.

---

## 🔘 Buttons

### Primary Button
```css
background: #000000
color: #F5F5EE
border-radius: 33554400px (pill shape)
padding: 12px 24px
font: Outfit, 14px, 500 weight
```

### Secondary Button (Outline)
```css
background: #F5F5EE
color: #8A8575
border: 1px solid #E5E5E0
border-radius: 0px (sharp)
padding: 8px 16px
font: Outfit, 13px, 500 weight
```

---

## 🎯 Component Styles

### Header
- **Background:** White (#FFFFFF)
- **Border:** 1px bottom (#E5E5E0)
- **Padding:** 24px vertical
- **Logo:** 40x40px square with sharp corners
- **Sticky:** Yes, stays on top

### Stats Bar
- **Background:** White
- **Border:** 1px bottom
- **Grid:** 4 columns
- **Stat Value:** 24px Outfit, 600 weight
- **Stat Label:** 12px Outfit, uppercase, 0.05em letter-spacing

### Job Cards
- **Background:** White
- **Border:** 1px solid (#E5E5E0)
- **Border Radius:** 0px (sharp)
- **Padding:** 32px
- **Hover:** Border turns black, slight lift (-2px)
- **Shadow:** Medium on hover

### Badges
- **Type:** Pill shape, primary color border
- **Location:** Pill shape, accent color border
- **Font:** Outfit, 12px, 500 weight
- **Padding:** 8px 16px

### Search Input
- **Background:** #F5F5EE (changes to white on focus)
- **Border:** 1px solid (#E5E5E0)
- **Border Radius:** 0px (sharp)
- **Focus:** Border turns black
- **Font:** Outfit, 14px

---

## ✨ Interactions

### Hover States
- **Job Cards:** Border → black, transform: translateY(-2px)
- **Buttons:** Slightly darker background
- **Links:** Color → accent (#2299DD)
- **Inputs:** Border → black, background → white

### Transitions
```css
Fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)
Normal: 250ms cubic-bezier(0.4, 0, 0.2, 1)
Slow: 350ms cubic-bezier(0.4, 0, 0.2, 1)
```

### Loading States
- **Spinner:** 40px, 2px border, black accent
- **Animation:** 1s linear infinite spin

---

## 📱 Responsive Breakpoints

### Desktop (>1024px)
- Jobs Grid: 3 columns
- Stats Grid: 4 columns

### Tablet (640px - 1024px)
- Jobs Grid: 2 columns
- Stats Grid: 2 columns

### Mobile (<640px)
- Jobs Grid: 1 column
- Stats Grid: 2 columns
- Header: Stacked layout
- Filters: Single column

---

## 🎨 Design Principles

### 1. Minimalism
- Sharp corners (0px radius) for architectural feel
- Minimal shadows
- Clean borders instead of depth
- Ample white space

### 2. Typography-Driven
- Outfit for UI clarity
- Source Serif 4 for readability
- Clear hierarchy through size and weight

### 3. Professional Tone
- Muted, sophisticated color palette
- Conservative animations
- Editorial layout for job details

### 4. Consistency
- 8px grid system throughout
- Same border widths (1px, 2px)
- Consistent spacing multiples

---

## 🖼️ Visual Elements

### Logo
- **Size:** 40x40px
- **Shape:** Square (sharp corners)
- **Background:** #FF6600 (orange)
- **Icon:** Briefcase emoji 💼

### Icons
- Unicode characters preferred
- Size: 16px-20px
- Color: Inherit from text

### Dividers
- **Thickness:** 1px or 2px
- **Color:** #E5E5E0
- **Style:** Solid, sharp

---

## 📊 Before & After Comparison

| Element | Before | After |
|---------|--------|-------|
| **Font** | System fonts | Outfit + Source Serif 4 |
| **Primary Color** | Blue (#2563eb) | Taupe (#8A8575) |
| **Background** | Light gray (#f8fafc) | Warm beige (#F5F5EE) |
| **Border Radius** | 8px-16px rounded | 0px sharp (architectural) |
| **Buttons** | Rounded pills | Black pills + sharp outline |
| **Cards** | Soft shadows | Sharp borders |
| **Spacing** | Varied | 8px grid system |
| **Typography** | Single font | Dual font system |

---

## 🚀 How to Use

### 1. View the Dashboard
```
http://localhost:5000
```

### 2. Check Design Elements
- **Header:** Clean, minimalist with new fonts
- **Stats:** Editorial layout with Outfit font
- **Job Cards:** Sharp corners, hover effects
- **Buttons:** Black pills for primary actions

### 3. Test Interactions
- Hover over job cards (border turns black)
- Click buttons (smooth transitions)
- View job details (editorial layout)
- Check mobile responsiveness

---

## 🎯 Key Features

✅ **Google Fonts Integration** - Outfit + Source Serif 4  
✅ **Premium Color Palette** - Sophisticated neutrals  
✅ **Sharp Architectural Design** - 0px border radius  
✅ **8px Spacing Grid** - Consistent throughout  
✅ **Minimalist Aesthetic** - Clean, professional  
✅ **Editorial Typography** - Magazine-quality layout  
✅ **Smooth Transitions** - Polished interactions  
✅ **Responsive Design** - Mobile, tablet, desktop  

---

## 📝 Files Modified

```
dashboard/static/css/style.css - Complete rewrite
dashboard/templates/index.html - Added Google Fonts
dashboard/templates/job_detail.html - Added Google Fonts
```

---

## 🎨 Color Palette Reference

```
Primary:   #8A8575 (Taupe)
Accent:    #2299DD (Blue)
Background:#F5F5EE (Warm Beige)
Surface:   #FFFFFF (White)
Text:      #16140F (Near Black)
Border:    #E5E5E0 (Light Taupe)
Black:     #000000
White:     #FFFFFF
```

---

**Design System Version:** 2.0  
**Inspired by:** Y Combinator Design Language  
**Last Updated:** April 1, 2026
