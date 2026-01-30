---
cssclasses:
  - table-wide
  - wide
---
# AGENDA EXTENDED: URLS-AND-CODE

## look up these urls
- product view einstiege: https://dasei.eu/ausbildung-theaterpaedagogik/kurs_einstiege_ins_theaterspiel
- checkout dasei (einstiege): https://dasei.eu/details?src=/agenda/einstiege-ins-theaterspiel-m18e
- product view grundlagen a,b,c,d: https://dasei.eu/ausbildung-theaterpaedagogik/grundlagenbildung

## source-code: understand the Checkout-Stepper
I decided to focus only on one input for code-inspection + design-questions: It is the checkout-stepper of the public-facing website (see the images referenced)

DO inspect all 13 vue-files at /files/agenda_extended -> the stepper-basis is inside DataViewDetails.vue
I think you understand it from from there

IF YOU NEED FURTHER FILES (vue-component-imports?) then list out the file-names and libs, I will provide them to you.

I think it holds some important findings:
- simplified page-header / hero-parsing for medium-size representations (as is needed for a basic implementation of the customer-journey)
- products - yaml (this partly gets created be agenda_dasei > controllers > mdc_generator.py **-> inspect + create a summary on it**) > inspect how 'products' are configured at the moment
- the wording and chaining of the steps itself and how they get configured:
	- md-2-catalog-rendering (inline-md inside yaml)
	- how the inputs are collected and prepared for hand-over to Odoo (formerly sharepoint)
