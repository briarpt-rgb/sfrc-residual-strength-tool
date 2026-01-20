SFRC Residual Flexural Strength Prediction App

This repository contains a Streamlit-based web application for predicting the residual flexural strengths $f_{R,1}$ and $f_{R,3}$ of steel-fiber-reinforced concrete (SFRC).

The application implements the empirical prediction models proposed in the associated manuscript and provides design-oriented outputs by converting mean predictions into characteristic and design values using calibrated reliability-based scaling factors.

Features


    Design-Oriented Prediction: Computes mean, characteristic, and design values of $f_{R,1}$ and $f_{R,3}$.
    Empirical Models: Implements optimized semi-empirical formulations calibrated against an extensive experimental database.
    Flexible Input Formats: Supports fiber volume fraction in percent or decimal form and concrete strength as $f_c$ or $f_{cu}$ (with automatic conversion).
    Validated Input Ranges: Enforces dataset-based limits and clearly flags extrapolation beyond the calibrated domain.
    Transparent Calculations: Displays governing equations and intermediate quantities for full traceability.
    Open-Access Web Interface: Runs entirely in a web browser with no local installation required for end users.

