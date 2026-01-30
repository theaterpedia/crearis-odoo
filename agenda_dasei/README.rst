=============
Agenda DASEi
=============

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

DASEi-specific extensions for the Crearis Agenda sync module. Provides course product
management, course-event mapping, partner status handling, and REST API for MDC
(Markdown Content) file generation.

**Table of contents**

.. contents::
   :local:

Features
========

Course Products
---------------

Syncs course products from SharePoint contacts list (entries starting with ``_``):

* **M18/N18 Programs**: Block and day courses for München/Nürnberg
* **ZR/ZT Profiles**: Advanced theatre pedagogy profiles
* **Offenes Programm**: Standalone events (SharePoint contact ID: 474)

Each product has:

* ``course_program``: M (München), N (Nürnberg), ZR, ZT
* ``course_year``: Cohort identifier (e.g., "18" for 2018)
* ``course_type``: block, day, or profile

Course-Event Mapping
--------------------

Links course products to their events via JSONB field ``course_event_ids``:

.. code-block:: json

   {
     "a0": {"event_id": 1328, "order": 1},
     "a1": {"event_id": 1178, "order": 2},
     "a2": {"event_id": 1190, "order": 3},
     "a3": {"event_id": 1346, "order": 4},
     "a4": {"event_id": 1294, "order": 5},
     "a5": {"event_id": 1295, "order": 6}
   }

The mapping is synced from SharePoint ``plan_veranstaltungsteilnehmer`` list.

Partner Status Mapping
----------------------

Maps SharePoint contact status to domain codes for login routing:

* ``dasei1``, ``dasei2``, ``dasei3``: Access levels based on course participation
* Computed ``highest_domaincode`` for determining user access tier

REST API
========

MDC Generation Endpoints
------------------------

Generate MDC (Markdown Content) files for the Nuxt.js website:

**Single Course MDC**

.. code-block::

   GET /api/v1/mdc/course/<product_ref>

Returns JSON with YAML content for a course product (e.g., ``m17e``, ``M18B``).

**Single Event MDC**

.. code-block::

   GET /api/v1/mdc/event/<event_id>

Returns JSON with YAML content for a standalone event (Offenes Programm).

**Bulk Export (ZIP)**

.. code-block::

   GET /api/v1/mdc/export?year=2026&include_courses=true&include_events=true

Returns ZIP file containing all MDC files for the specified year.

**List Courses**

.. code-block::

   GET /api/v1/mdc/courses

Returns JSON array of all course products with event counts.

**List Open Events**

.. code-block::

   GET /api/v1/mdc/events?year=2026

Returns JSON array of Offenes Programm events for the specified year.

MDC Rendering Details
---------------------

The MDC generator synthesizes YAML fields with intelligent data formatting from Odoo records.

**Single Event YAML (Offenes Programm)**

+-------------------+---------------------------------------------------------------+
| Field             | Rendering Logic                                               |
+===================+===============================================================+
| ``publish``       | Always ``draft`` (manual review before publish)               |
+-------------------+---------------------------------------------------------------+
| ``id``            | ``{shortcode}_{ms_id}`` e.g., ``lr_1568``                     |
+-------------------+---------------------------------------------------------------+
| ``heading``       | ``ORT D.-D.M // event.name`` with location abbrev             |
|                   | e.g., ``MÜ 4.-6.4 // Methodenworkshop **Titel**``             |
+-------------------+---------------------------------------------------------------+
| ``title``         | Extracted from ``**bold**`` pattern in event.name             |
+-------------------+---------------------------------------------------------------+
| ``teaser``        | From ``event.teasertext`` or ``event_type.template_teasertext``|
+-------------------+---------------------------------------------------------------+
| ``description``   | From ``event.description`` (Markup → string conversion)       |
+-------------------+---------------------------------------------------------------+
| ``start/ende``    | ISO date format ``YYYY-MM-DD``                                |
+-------------------+---------------------------------------------------------------+
| ``hero.height``   | Fixed ``prominent``                                           |
+-------------------+---------------------------------------------------------------+
| ``hero.content_y``| Fixed ``top``                                                 |
+-------------------+---------------------------------------------------------------+
| ``hero.cta.title``| Fixed ``jetzt anmelden``                                      |
+-------------------+---------------------------------------------------------------+
| ``image.alt``     | Extracted title or event_type heading                         |
+-------------------+---------------------------------------------------------------+
| ``image.src``     | Cloudinary URL from ``event.cimg`` or ``event_type.cimg``     |
+-------------------+---------------------------------------------------------------+
| ``details.programm.info.struktur`` | ``event.schedule`` + location address        |
+-------------------+---------------------------------------------------------------+
| ``details.konditionen.info.kosten``| Template with placeholder price              |
+-------------------+---------------------------------------------------------------+
| ``details.konditionen.info.storno``| Standard cancellation policy text            |
+-------------------+---------------------------------------------------------------+

Location abbreviations: ``MÜ`` (München), ``NÜ`` (Nürnberg)

**Course YAML (Block/Tag Programs)**

+-------------------+---------------------------------------------------------------+
| Field             | Rendering Logic                                               |
+===================+===============================================================+
| ``shortcode``     | From ``product.default_code`` lowercase                       |
+-------------------+---------------------------------------------------------------+
| ``heading``       | ``**Title** Location D.M.Y - D.M.Y // Type``                  |
|                   | e.g., ``**Einstiege** München 8.1.2026 - 6.1.2027 // Tageskurs``|
+-------------------+---------------------------------------------------------------+
| ``title``         | ``Einstiege ins Theaterspiel`` (block/day courses)            |
+-------------------+---------------------------------------------------------------+
| ``start/end``     | Course date range from first/last event                       |
+-------------------+---------------------------------------------------------------+
| ``tag``           | Fixed ``course``                                              |
+-------------------+---------------------------------------------------------------+
| ``description``   | Synthesized: ``Weiterbildung Theaterpädagogik - Kurs {CODE}`` |
|                   | ``{Location} {dates} // {Type} {Location}``                   |
+-------------------+---------------------------------------------------------------+
| ``views``         | ``[product, details]``                                        |
+-------------------+---------------------------------------------------------------+
| ``details.programm.info.struktur`` | Template based on course_type (block/day)    |
+-------------------+---------------------------------------------------------------+
| ``product.header``| ``## {N} Kurseinheiten`` + intro text                         |
+-------------------+---------------------------------------------------------------+
| ``product.footer``| ``## MÄR - DEZ 2026 // München **Title**``                    |
|                   | (German month abbreviations)                                  |
+-------------------+---------------------------------------------------------------+

**Course Items (Events within Course)**

+-------------------+---------------------------------------------------------------+
| Field             | Rendering Logic                                               |
+===================+===============================================================+
| ``tag``           | ``Do., 25.9. bis So., 28.9 + Abende online``                  |
|                   | German weekday abbrev + date range + online suffix            |
+-------------------+---------------------------------------------------------------+
| ``title``         | From ``event.name`` or ``event_type.template_heading``        |
+-------------------+---------------------------------------------------------------+
| ``body``          | From ``event.teasertext`` (Markup → string)                   |
+-------------------+---------------------------------------------------------------+
| ``image.url``     | Cloudinary URL with width transform                           |
+-------------------+---------------------------------------------------------------+
| ``image.caption`` | ``Theaterpädagogik {SHORTCODE}``                              |
+-------------------+---------------------------------------------------------------+
| ``start/ende``    | ISO datetime format                                           |
+-------------------+---------------------------------------------------------------+
| ``ort``           | Formatted address from ``event.address_id``                   |
+-------------------+---------------------------------------------------------------+
| ``ablauf``        | From ``event.schedule``                                       |
+-------------------+---------------------------------------------------------------+
| ``mit``           | Comma-joined ``event.user_id.name``                           |
+-------------------+---------------------------------------------------------------+

German month abbreviations: JAN, FEB, MÄR, APR, MAI, JUN, JUL, AUG, SEP, OKT, NOV, DEZ

Configuration
=============

SharePoint Lists
----------------

The module syncs from these SharePoint lists (configured on ``res.company``):

* ``ms_list_contacts``: Course products (contacts starting with ``_``)
* ``ms_list_veranstaltungsteilnehmer``: Course-event relationships
* ``ms_list_kursteilnehmer``: Course participations

Synced Product IDs
------------------

Only specific SharePoint contact IDs are synced as products:

.. code-block:: python

   SYNC_PRODUCT_IDS = ['530', '532', '534', '536', '512', '550', '474']
   # M18: 530 (Block), 534 (Tag)
   # N18: 532 (Block), 536 (Tag)
   # ZR: 512, ZT: 550
   # Offenes Programm: 474

Product Default Codes
---------------------

Each synced product gets an auto-generated ``default_code`` (internal reference):

+----------------------------+---------------+--------------+
| Product                    | default_code  | ms_contact_id|
+============================+===============+==============+
| M18_Blockprogramm München  | m18b          | 530          |
+----------------------------+---------------+--------------+
| M18_Tageskurs München      | m18t          | 534          |
+----------------------------+---------------+--------------+
| N18_Blockprogramm Nürnberg | n18b          | 532          |
+----------------------------+---------------+--------------+
| N18_Tageskurs Nürnberg     | n18t          | 536          |
+----------------------------+---------------+--------------+
| Profil ZR 2026-2028        | z15r          | 512          |
+----------------------------+---------------+--------------+
| Profil ZT 2026-2028        | z15t          | 550          |
+----------------------------+---------------+--------------+
| Offenes Programm           | op            | 474          |
+----------------------------+---------------+--------------+

The default_code is used for API lookups and URL slugs (e.g., ``/api/v1/mdc/course/m18b``).

Usage
=====

Triggering Sync
---------------

The course-event mapping syncs automatically as part of ``sync_all()``:

.. code-block:: python

   sync_engine = self.env['crearis.agenda.sync']
   sync_engine.sync_all(company)

This will:

1. Sync products from SharePoint contacts
2. Sync event types and events (parent module)
3. Sync course-event mapping from ``plan_veranstaltungsteilnehmer``
4. Sync course participations

Manual Event Mapping
--------------------

To manually set course events on a product:

.. code-block:: python

   product = self.env['product.template'].browse(123)
   product.write({
       'course_event_ids': {
           'a0': {'event_id': 1328, 'order': 1},
           'a1': {'event_id': 1178, 'order': 2},
       }
   })

Getting Ordered Events
----------------------

.. code-block:: python

   product = self.env['product.template'].browse(123)
   events = product.get_course_events_ordered()
   for event in events:
       print(f"{event.event_type_id.name}: {event.name}")

Known Issues & TODOs
====================

.. warning::

   The following items need attention before production deployment.

API Security (HIGH PRIORITY)
----------------------------

**Current state**: API endpoints use ``auth='public'`` - accessible without authentication.

**TODO**: Enable API key validation:

1. Set system parameter ``dasei.mdc_api_key`` with a secure key
2. Uncomment validation in ``mdc_generator.py``:

   .. code-block:: python

      # In generate_course_mdc() and other endpoints:
      if not self._validate_api_key():
          return self._json_response({'error': 'Invalid API key'}, 401)

3. Pass header ``X-API-Key: <your-key>`` with API requests

**Alternative**: Use Odoo's built-in ``auth='api_key'`` authentication.

Event Field Availability
------------------------

The MDC generator checks for fields that may not exist on ``event.event``:

* ``teasertext``: Synced from SharePoint, may need ``crearis_agenda`` dependency
* ``cimg``: Cloudinary image code
* ``schedule``: Event schedule text

Ensure these fields are properly synced before using MDC generation.

YAML Dependency (Optional)
--------------------------

The module uses PyYAML for proper YAML generation. If not installed, it falls back
to JSON format. For proper MDC compatibility, install PyYAML:

.. code-block:: bash

   pip install PyYAML

The module will work without it, but the output format will be JSON instead of YAML.

Offenes Programm Detection
--------------------------

Currently detects by SharePoint contact ID (``474``). Consider adding a boolean
field ``is_open_program`` for clarity.

Sync Performance
----------------

The ``sync_course_event_mapping()`` method loads all items from
``plan_veranstaltungsteilnehmer``. For large lists, consider:

* Adding pagination
* Filtering by modified date
* Caching results

Dependencies
============

* ``crearis_agenda``: Base sync engine and SharePoint integration
* ``product``: Product template model
* ``event``: Event management

External Python dependencies:

* ``PyYAML``: For YAML generation (optional, falls back to JSON)

Credits
=======

Authors
-------

* Theaterpedia

Maintainers
-----------

This module is maintained by Theaterpedia.

.. image:: https://theaterpedia.org/logo.png
   :alt: Theaterpedia
   :target: https://theaterpedia.org

Contributors
------------

* Theaterpedia Development Team
