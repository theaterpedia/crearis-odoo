Now the goal is to display the products from Dasei Courses on a existing Nuxt.js website. 
The core tasks are:
1. analyze the markdown files that define the Dasei Course products
   - on the nuxt.js-project: saved under /agenda/ .. einstiege-ins-theaterspiel_m17e.md and einstiege-ins-theaterspiel_n17e.md, einstiege-ins-theaterspiel_m17b.md, etc.
   - on the nuxt.js-project: nuxt-content-page that references these md-files: 2.kurs_einstiege_ins_theaterspiel.md
2. analyze the existing simple checkout process at route /details[] on the Nuxt.js website
   - inspect the url: https://www.dasei.eu/details?src=/agenda/einstiege-ins-theaterspiel-m17e
   - inspect the code that handles this route and the checkout process: DataViewdetails.vue
   - inspect the product-url: https://www.dasei.eu/ausbildung-theaterpaedagogik/kurs_einstiege_ins_theaterspiel
   - inspect the code that handles this product page: DataViewProduct.vue

3. inspect the products, sales, and checkout prepared in the current odoo backend
    -> understand it from the installed modules that are listed as dependencies for the crearis-module (especially sales, products)
4. remember how the module agenda_dasei prepares course-events as odoo products

6. find out how odoo products can hold the course-event-information that are present on the sharepoint-based course-event-database (see the docs: dasei_course_events_via_sharepoint.md) )

5. create 3 documents that make 3 proposals (save under chat/dasei)
   5a. how to link the nuxt-website product-page to the odoo product
   5b. how to link the nuxt-website checkout to the odoo sales/checkout
   5c. how to create the yaml-files for courses M18, N18 (file-suffixes: m18b, m18e, n18b, n18e) using templates

NOTE1: We changed the md-file-names to use underscores instead of hyphens for the course suffix.
NOTE2: process 5c should be done using templates, so that the future courses can be created easily. It starts with 2 yaml-templates (for the e-Variant and the b-Variant of the courses) that are generatedfrom existing markdown files
NOTE3: documents 5a and 5b instructs code-automation on the nuxt-project.

---

Questions Before Implementation
Q1: Odoo Product Linking Strategy
The markdown files currently don't reference Odoo. Do you want:

A) Add odoo_product_id field to the markdown frontmatter that maps to product.template.id in Odoo?
B) Use a convention-based mapping (e.g., shortcode: m17e → product with default_code='M17E')?
C) Create a separate mapping file/table?
Q2: Checkout Integration Depth
For linking the Nuxt checkout to Odoo sales:

A) Keep Azure Logic App and have it create Odoo sales orders via API?
B) Replace Azure Logic App with direct Odoo API calls from Nuxt (using VSF/GraphQL)?
C) Hybrid: Azure Logic App writes to both SharePoint AND Odoo?
Q3: Course Events vs Products
The markdown items contain individual course events (a0-a5). Should these:

A) Each become separate event.event records in Odoo (linked to the course product)?
B) Stay only in the markdown, with Odoo product representing the whole course?
C) Be synced bidirectionally (Odoo events ↔ markdown items)?
Q4: M18/N18 Template Generation
For task 5c (creating m18b, m18e, n18b, n18e files):

The m18b file in 2025-12-27 seems to be a draft (shortcode says m17b but dates are for 2025 spring)
Should the templates be YAML (as you mentioned) or keep them as full .mdc files?
What date ranges and locations should M18/N18 courses have?
Q5: SharePoint Role
The doc mentions dasei_course_events_via_sharepoint.md but that file doesn't exist. What course-event-information from SharePoint should be preserved in Odoo products? Specifically:

Are there additional fields beyond what's in the markdown files?
Should we sync the event dates from SharePoint or from the markdown files?

---

Q2: A // Q3: A
### Q1: I give more detail on that:
in the current installation on sharepoint we are still using on old api.
It is on a different site (https://dasei.sharepoint.com/sites/api) than the one used for syncing in the current project (https://dasei.sharepoint.com/sites/dasei-website).
This should be hardcoded in the documents for 5a and 5b.
Once it is confirmed working, we will refactor the existing PowerAutomate-flows to use the new api-site.

### Q4: I give more detail on that: 
Ignore the m18b, create the templates from the m17 files. The templates should be mdc. M18/N18 has the same date-ranges and locations as the m17 files, but exactly one year later. 

### Q5: I give more detail on that: 
It should be done in a way that all relevant event data is synced from sharepoint to odoo products + events, so that the nuxt-website can display the product-data from odoo.
At the moment we are in alpha-phase, crearis_agenda syncs using the 'slave' mode (understand that again), but soon we want to switch to 'master' mode, so that odoo is the main-database for course-events and products. So this switch should be prepared already now.
For instance we want to update the course descriptions in odoo-products, event-dates or details so that the nuxt-website displays them from odoo, as well as sharepoint picks up the changes.

### NEW API URL:
The Sharepoint-api has changed, here are the new URLs for the PowerAutomate-flows -> this has to be added to the instructions in the documents for 5a and 5b.
https://default430c53e6651e45efa53c004ea96dd2.16.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dW-If8W3p85RTFP0mE2PD-r0sgu9opFXOmmwKuJ7xwU


---

TASK 1 is well designed: Implement it with 'more metadata'.  // TASK 2 