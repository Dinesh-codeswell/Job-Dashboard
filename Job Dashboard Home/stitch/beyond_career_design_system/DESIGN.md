# Design System Document

## 1. Overview & Creative North Star: "The Obsidian Architect"
This design system is not a collection of components; it is a philosophy of light and space. Our Creative North Star, **The Obsidian Architect**, focuses on the interplay between infinite depth and precision-engineered light. We move away from the "flat web" by treating the interface as a physical environment carved out of dark matter.

To achieve a "High-End Editorial" feel, we reject the standard rigid grid in favor of **Intentional Asymmetry**. By utilizing generous whitespace (the "breathing room" of luxury) and overlapping elements that break container boundaries, we create a sense of motion and tech-forward sophistication. We don't just display information; we curate an experience.

---

## 2. Colors & Atmospheric Depth
The palette is rooted in absolute blacks and deep charcoals, punctuated by a surgical application of Emerald Green. 

### The "No-Line" Rule
**Borders are a failure of hierarchy.** Within this system, 1px solid borders for sectioning are strictly prohibited. Boundaries must be defined solely through:
1.  **Background Color Shifts:** Placing a `surface_container_low` section against a `surface` background.
2.  **Tonal Transitions:** Using subtle value shifts to imply a change in context.

### Surface Hierarchy & Nesting
Treat the UI as stacked sheets of obsidian. Use the `surface_container` tiers to create "nested" depth:
*   **Base:** `surface` (#131313) for the main canvas.
*   **Lowered:** `surface_container_lowest` (#0e0e0e) for recessed areas like sidebars or footer wells.
*   **Elevated:** `surface_container_high` (#2a2a2a) for interactive modules or primary cards.

### The "Glass & Gradient" Rule
To prevent the UI from feeling "heavy," use Glassmorphism for floating elements (Modals, Popovers). Apply a semi-transparent `surface_variant` with a 20px-40px backdrop-blur. 
*   **Signature Textures:** For high-impact CTAs, use a subtle linear gradient transitioning from `primary_container` (#008359) to `primary` (#73daa9) at a 135-degree angle. This adds "visual soul" that flat hex codes cannot replicate.

---

## 3. Typography: Editorial Precision
We utilize a dual-sans-serif approach to balance authority with readability.

*   **Display & Headlines (Manrope):** Chosen for its geometric purity and modern "Neue Haas" feel. Use `display-lg` and `display-md` with tight letter-spacing (-0.02em) to create an editorial impact.
*   **Body & Labels (Inter):** The workhorse of the system. Inter provides exceptional legibility at small sizes. Use `body-md` for standard reading and `label-md` for technical metadata.

**Hierarchy Note:** Always maintain a high contrast between your headlines and body text. A `headline-lg` should feel significantly more "massive" than the accompanying `body-lg` to guide the eye through the content narrative.

---

## 4. Elevation & Depth: Tonal Layering
We do not use shadows to mimic 2010-era skeuomorphism. We use them to simulate ambient light in a dark room.

*   **The Layering Principle:** Place `surface_container_low` (#1b1b1b) cards on a `surface` background for a "soft lift."
*   **Ambient Shadows:** For floating elements, use extra-diffused shadows. 
    *   *Spec:* `0px 24px 48px rgba(0, 0, 0, 0.4)`. The shadow should feel like a soft glow of darkness rather than a hard edge.
*   **The "Ghost Border" Fallback:** If accessibility requires a stroke, use `outline_variant` (#3e4942) at 15% opacity. Never use 100% opaque borders.
*   **Glassmorphism:** Use `surface_bright` (#393939) at 60% opacity with a heavy backdrop blur for navigation bars to let content "bleed" through as the user scrolls, maintaining a sense of place.

---

## 5. Components

### Buttons
*   **Primary:** High-contrast Emerald. Background: `primary_container` (#008359); Text: `on_primary_container` (#e7ffef). 8px roundedness.
*   **Secondary:** Ghost style. No background, `outline` stroke (at 20% opacity), `on_surface` text.
*   **Interaction:** On hover, primary buttons should utilize the `primary_fixed` (#90f7c4) color for a subtle "bloom" effect.

### Input Fields
*   **Styling:** Background: `surface_container_highest` (#353535). No border.
*   **States:** On focus, transition the background to `surface_bright` (#393939) and add a 1px "Ghost Border" using the `primary` (#73daa9) token at 30% opacity.

### Cards & Lists
*   **The Divider Ban:** Strictly forbid 1px lines between list items. Use the `8` (2rem) or `10` (2.5rem) spacing scale to separate items, or alternate background shades between `surface_container_low` and `surface_container_high`.
*   **Featured Cards:** Use a subtle "inner glow" by applying a 1px top-only border in `outline_variant` at 20% opacity to simulate light hitting the top edge of the obsidian sheet.

### Additional Signature Components
*   **The Progress Blade:** A slim, 2px tall emerald line (`primary`) that runs across the very top of the viewport or container to indicate loading or progress, maintaining the tech-forward aesthetic.

---

## 6. Do's and Don'ts

### Do:
*   **Embrace the Void:** Use the `#000000` background to make the emerald accents and white typography "pop" with cinematic intensity.
*   **Asymmetric Grids:** Offset images or text blocks by one or two columns to break the "template" feel.
*   **Intentional Whitespace:** Use the `20` (5rem) and `24` (6rem) spacing tokens between major sections.

### Don't:
*   **Never use pure white (#FFFFFF) for body text:** Use `on_surface` (#e2e2e2) to reduce eye strain and maintain the premium dark aesthetic.
*   **No "Boxy" Layouts:** Avoid putting every piece of content inside a visible container. Let the typography and spacing define the sections.
*   **Avoid High-Saturation Grays:** Stick to the provided neutral tokens which are slightly tinted to ensure the dark theme feels "expensive" rather than "default."