# 🎨 Google Stitch Design Prompt - Job Dashboard Redesign

## 📋 Overview

This directory contains a comprehensive JSON prompt (`google_stitch_prompt.json`) that describes your entire LinkedIn Jobs Dashboard website for AI-powered design generation using Google Stitch or similar AI design tools.

---

## 🎯 Purpose

The JSON prompt provides complete context about:
- **Website structure** and layout
- **All pages** (dashboard, job detail, about)
- **Component specifications** (cards, buttons, filters, etc.)
- **Data structure** and job parameters
- **Design system** (colors, typography, spacing)
- **Responsive breakpoints** (mobile, tablet, desktop)
- **Accessibility requirements** (WCAG AA compliance)
- **Performance requirements** (Lighthouse scores)
- **Reference inspiration** (LinkedIn, Otta, Product Space)

---

## 📁 File Structure

```
C:\linkedin_scraper\
├── google_stitch_prompt.json    # Complete design specification
└── STITCH_README.md             # This file (usage guide)
```

---

## 🚀 How to Use

### **Step 1: Prepare Your Reference Images (Optional)**

Collect screenshots or links to job dashboards you admire:
- LinkedIn Jobs
- Otta
- Product Space
- Wellfound
- Any other inspiration

### **Step 2: Load the JSON Prompt**

**Option A: Google Stitch (when available)**
```
1. Open Google Stitch
2. Import/Upload: google_stitch_prompt.json
3. Review the parsed specifications
4. Add your reference images
5. Generate mockups
```

**Option B: Other AI Design Tools**
```
1. Copy contents of google_stitch_prompt.json
2. Paste into AI tool (ChatGPT, Claude, etc.)
3. Add instruction: "Generate UI mockups based on these specifications"
4. Provide reference images if available
5. Iterate on generated designs
```

**Option C: Human Designer**
```
1. Share google_stitch_prompt.json with designer
2. Review specifications together
3. Discuss design direction
4. Create mockups in Figma/Sketch/Adobe XD
```

---

## 📊 What's Included in the JSON

### **1. Project Overview**
```json
{
  "project": {
    "name": "LinkedIn Jobs Dashboard - India",
    "type": "Job Aggregation Dashboard",
    "goal": "Redesign and optimize UI/UX..."
  }
}
```

### **2. Design System**
- Color palette (primary, accent, background, etc.)
- Typography (fonts, sizes, weights)
- Spacing scale (8px base unit)
- Border radius (0px to 9999px)
- Shadows/elevation (5 levels)

### **3. Complete Page Specifications**

#### **Home Dashboard (`/`)**
- Header with logo and actions
- Stats bar (4 metrics)
- Filters section (search, city, type)
- Filter chips (active filters)
- Jobs grid (responsive cards)
- Pagination
- Loading states
- Empty states
- Error states

#### **Job Detail Page (`/job/:id`)**
- Back button
- Job header (title, company, badges)
- Job meta info bar
- Job description
- Requirements section
- Company info sidebar
- Apply button
- Share/Bookmark actions

#### **About Page (`/about`)**
- Information sections
- Feature lists
- Target roles
- Target cities
- How to use steps

### **4. Component Library**
Detailed specs for:
- Buttons (primary, outline, sizes, states)
- Cards (job cards, stat cards, info cards)
- Badges (type, location, new, salary)
- Inputs (search, selects)
- Meta items (icons + text)
- Filter chips
- Pagination
- Loading skeletons
- Toast notifications

### **5. Data Structure**
Complete job object schema:
```json
{
  "id": "string",
  "job_title": "string",
  "company": "string",
  "employment_type": "string",
  "location": "string",
  "posted_date": "datetime",
  "linkedin_url": "url",
  "job_description": "text",
  "search_city": "string",
  "date_added": "datetime",
  "salary_range": "object",
  "experience_level": "string",
  "is_remote": "boolean",
  "skills": "array"
}
```

### **6. API Endpoints**
- GET `/api/jobs` - Get paginated jobs
- GET `/api/jobs/:id` - Get job details
- GET `/api/stats` - Get dashboard stats
- GET `/api/cities` - Get cities list
- GET `/api/employment-types` - Get employment types

### **7. Responsive Breakpoints**
- **Mobile** (<640px): 1 column, stacked layout
- **Tablet** (641-1024px): 2 columns
- **Desktop** (>1025px): 3 columns, full features

### **8. Accessibility Requirements**
- WCAG 2.1 AA compliance
- Keyboard navigation
- Focus states
- Color contrast ratios
- Screen reader compatibility
- Touch target sizes (44px minimum)

### **9. Performance Requirements**
- Lighthouse scores (90+ across all categories)
- Core Web Vitals targets
- Optimization strategies (lazy loading, skeleton loaders, etc.)

### **10. Reference Inspiration**
Links and liked aspects from:
- LinkedIn Jobs
- Otta
- Product Space
- Wellfound

---

## 🎨 Design Goals

### **Primary Goals**
1. Match or exceed quality of LinkedIn, Otta, and Product Space
2. Make job scanning fast and efficient (3-second rule)
3. Create professional, trustworthy appearance
4. Ensure mobile-first responsive design
5. Achieve 90+ Lighthouse scores

### **Secondary Goals**
1. Add delightful micro-interactions
2. Implement dark mode support
3. Add salary transparency where available
4. Create shareable job cards
5. Add company culture indicators

---

## 📝 Example Prompts to Use with the JSON

### **For Complete Redesign**
```
Using the specifications in google_stitch_prompt.json, generate modern, 
professional mockups for a job dashboard. Focus on creating a clean, 
scannable interface that matches top-tier job boards like LinkedIn and Otta.

Generate:
1. Desktop dashboard view
2. Mobile dashboard view
3. Desktop job detail page
4. Mobile job detail page
5. Component library

Style: Modern, professional, trustworthy
Colors: Use provided palette or suggest improvements
Typography: Clean, readable, professional
```

### **For Specific Component**
```
Based on the job card specifications in the JSON, generate 5 different 
job card design variations. Each should:
- Be scannable in 3 seconds
- Show: title, company, location, posted date, employment type
- Include a "NEW" badge for jobs <24 hours old
- Have clear visual hierarchy
- Work on mobile and desktop

Provide both light and dark mode versions.
```

### **For Layout Optimization**
```
Review the current dashboard layout in the JSON. Suggest 3 alternative 
layouts that improve:
1. Information hierarchy
2. Scannability
3. Filter visibility
4. Mobile experience

Provide wireframes for each option with pros/cons.
```

### **For Color Scheme Update**
```
Using the current color palette as a base, suggest an updated, more 
modern color scheme that:
- Maintains professionalism
- Improves accessibility (WCAG AA contrast)
- Feels more tech-forward
- Works for both light and dark modes

Provide color tokens and usage examples.
```

---

## 🔄 Iteration Process

### **Round 1: Concept Generation**
- Generate 3-5 different design directions
- Review overall style and feel
- Select preferred direction

### **Round 2: Refinement**
- Refine selected direction
- Adjust colors, typography, spacing
- Improve component designs

### **Round 3: Detail Polish**
- Add micro-interactions
- Refine hover states
- Add loading/empty/error states
- Create responsive variants

### **Round 4: Final Delivery**
- Export design tokens
- Generate style guide
- Create component documentation
- Prepare handoff materials

---

## 📤 Expected Deliverables

After working with Google Stitch, you should have:

1. **Desktop Mockups**
   - Home dashboard
   - Job detail page
   - About page

2. **Mobile Mockups**
   - Home dashboard (mobile)
   - Job detail page (mobile)

3. **Component Library**
   - Buttons (all states)
   - Cards (all variants)
   - Badges (all types)
   - Inputs (all states)
   - Navigation elements

4. **Design Tokens**
   - Colors (with dark mode variants)
   - Typography scale
   - Spacing scale
   - Border radius
   - Shadows/elevation

5. **Interaction Specifications**
   - Hover states
   - Active states
   - Focus states
   - Transitions/animations
   - Loading states

6. **Responsive Documentation**
   - Mobile layouts
   - Tablet layouts
   - Desktop layouts
   - Breakpoint behaviors

---

## 🛠️ Tools to Use

### **AI-Powered Design**
- **Google Stitch** (when available)
- **Galileo AI** (galileo.ai)
- **Uizard** (uizard.io)
- **Figma AI** (figma.com/ai)
- **ChatGPT + Vision** (for feedback)

### **Traditional Design Tools**
- **Figma** (Recommended for implementation)
- **Sketch**
- **Adobe XD**
- **Framer**

### **Prototyping**
- **Figma Prototype**
- **Principle**
- **ProtoPie**
- **Framer**

---

## ✅ Quality Checklist

Before finalizing designs, verify:

- [ ] Matches or exceeds LinkedIn/Otta quality
- [ ] Job cards scannable in 3 seconds
- [ ] Clear visual hierarchy throughout
- [ ] All interactive elements clearly distinguishable
- [ ] Mobile-first responsive design
- [ ] Accessibility compliant (WCAG AA)
- [ ] Dark mode support (if included)
- [ ] Loading states designed
- [ ] Empty states designed
- [ ] Error states designed
- [ ] All components documented
- [ ] Design tokens exported
- [ ] Handoff-ready for developers

---

## 📞 Next Steps After Design

1. **Review designs** with stakeholders
2. **Gather feedback** and iterate
3. **Finalize designs** and export assets
4. **Create implementation plan**
5. **Update CSS** with new design tokens
6. **Implement components** one by one
7. **Test thoroughly** (accessibility, performance)
8. **Deploy** and monitor metrics

---

## 💡 Tips for Best Results

1. **Be specific** about what you want
2. **Provide examples** of designs you like
3. **Iterate quickly** - generate multiple variations
4. **Test on real devices** - mobile, tablet, desktop
5. **Check accessibility** - contrast, focus states, keyboard nav
6. **Consider performance** - don't over-design animations
7. **Think responsive** - design for all screen sizes
8. **Document everything** - future you will thank you

---

## 📚 Additional Resources

- **Google Material Design**: material.io/design
- **Apple Human Interface**: developer.apple.com/design
- **WCAG Guidelines**: w3.org/WAI/WCAG21/quickref
- **Lighthouse**: web.dev/lighthouse-overview
- **Web Vitals**: web.dev/vitals

---

**Ready to redesign?** Open `google_stitch_prompt.json` in your AI design tool and start generating! 🎨

For questions or clarifications about the specifications, refer to the detailed JSON comments or the project documentation files.
