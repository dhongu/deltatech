Watermark Field Base
====================

This module provides a base field for watermark images or text within Odoo. It's designed to act as a centralized storage and configuration point for watermarking functionalities used across different areas of the system, particularly in reports and on the website.

Key Features
============

1.  **Centralized Watermark Storage**:
    *   Adds a dedicated **Watermark** field (usually on the Company model).
    *   Provides a standardized place to upload and manage the image or define the text used for watermarking corporate documents or media.

2.  **Configuration Settings**:
    *   Integrates with Odoo's standard configuration settings for easy management.
    *   Allows administrators to quickly update the corporate watermark globally.

3.  **Foundation for Extensions**:
    *    Acts as a necessary dependency for more specific watermarking modules, such as those that apply watermarks to website images or generated PDF reports.

Usage
=====

1.  Navigate to **Settings > General Settings**.
2.  Locate the **Watermark** section (if configured) or open the **Company** record.
3.  Upload the desired image or enter the text you wish to use as a watermark.
4.  Install other modules that depend on this base module (e.g., `deltatech_website_watermark`) to see the watermark applied in specific contexts.

WARNING:

   This module provides the necessary fields and configuration but does not apply the watermark by itself. It requires additional extension modules to perform the actual watermarking on specific documents or images.
