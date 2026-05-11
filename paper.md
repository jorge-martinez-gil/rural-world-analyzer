---
title: "Rural World Analyzer: Measuring civic amenity accessibility in rural and semi-urban territories"
tags:
  - rural studies
  - geospatial analytics
  - OpenStreetMap
  - Streamlit
  - accessibility
authors:
  - name: Jorge Martinez-Gil
    orcid: 0000-0002-5983-2314
    affiliation: 1
affiliations:
  - name: Software Competence Center Hagenberg, Austria
    index: 1
date: 11 March 2025
---

# Summary

Rural World Analyzer is an open-source Streamlit application for the exploratory analysis of civic amenities in rural and semi-urban territories. The software queries OpenStreetMap through OSMnx, transforms retrieved features into interactive geospatial visualizations, and summarizes local service availability through a reproducible analytical workflow. The application targets researchers in rural development, territorial cohesion, smart villages, and digital public service provision, offering an accessible interface for comparing places that are often underrepresented in mainstream urban analytics platforms.

# Statement of Need

Scholars and practitioners frequently evaluate rural resilience by examining the distribution of services such as schools, healthcare, transport infrastructure, and financial institutions. However, rural amenity assessment often requires advanced GIS tooling, fragmented datasets, or manual inspection workflows that are difficult to reproduce across case studies. Rural World Analyzer addresses this gap by providing an openly available, browser-based environment for rapidly estimating the breadth and diversity of civic amenities around a selected point. By lowering the technical barrier to exploratory geospatial assessment, the software helps researchers build comparative datasets, communicate findings visually, and support evidence-based discussions on service access in peripheral regions.

# Rural Accessibility Index Methodology

The central contribution of the software is the Rural Accessibility Index (RAI), a composite score designed to summarize service provision in a compact and interpretable form. The metric combines three components: the total number of amenities detected within a user-defined radius, the number of distinct amenity categories, and the Shannon diversity index of amenity types. Formally, the implementation computes:

`RAI = min(100, N × 0.4 + H × 30 + K × 2)`

where `N` is the total amenity count, `H` is Shannon entropy derived from amenity-type proportions, and `K` is the number of unique amenity categories. This formulation rewards areas that provide both numerous and diverse services while preventing highly concentrated inventories from dominating the score. When only a single amenity category is present, entropy collapses to zero, preserving interpretability without introducing undefined values.

# Functionality

The application supports multiple analytical tasks that are particularly relevant for reproducible rural research. Users can select from geographically diverse example locations spanning Europe, Africa, Asia, and the Americas or provide custom coordinates. Amenities can be filtered by a broad range of OpenStreetMap amenity classes, visualized on an interactive Folium map, and rendered as density heatmaps and clustered markers. Complementary Plotly charts summarize amenity-type frequencies, while summary metrics report total amenities, unique categories, RAI, and Shannon diversity side by side.

To encourage comparative analysis, Rural World Analyzer includes an area comparison mode that renders two study areas in parallel with synchronized parameters. The software also provides CSV and GeoJSON export options so that downstream statistical analysis, mapping, or archival workflows can be reproduced in external environments. Repository metadata files such as `CITATION.cff` and `.zenodo.json` further improve software citation and long-term scholarly visibility.

# References

Martinez-Gil, Jorge, Mario Pichler, Noemi Lechat, Gianluca Lentini, Nina Cvar, Jure Trilar, Antonio Bucchiarone, and Annapaola Marconi. 2025. “An Overview of Civic Engagement Tools for Rural Communities.” *Open Research Europe* 4 (195): 195.
