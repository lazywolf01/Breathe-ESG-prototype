# Sources

## SAP fuel and procurement

Researched format: SAP S/4HANA material document/OData style extraction for material movement and goods receipt data. SAP documents the Material Document API as an OData service for material document operations, and SAP Cloud SDK references `API_MATERIAL_DOCUMENT_SRV` for material documents such as goods receipts and transfers.

What I learned: the useful operational fields for this prototype are document/year identity, posting date, plant, material, movement type, quantity, unit, and currency/spend. Plant and material codes need lookup tables before they mean anything to an ESG analyst.

Sample data: `sample_data/sap_material_documents.csv` includes diesel/petrol quantities, procurement spend, SAP-like material IDs, movement types, plant codes, and one missing plant.

What would break: customer-specific SAP configuration, language/localized columns, batch splits, reversed documents, unit conversions, and PO/vendor joins.

References:

- SAP Help Portal, OData services for SAP S/4HANA Cloud: https://help.sap.com/docs/SAP_S4HANA_CLOUD/3f57e7df4a114edabffe8b2d581a59ed/013f0f9ef9dc48daa3c4709ab8860333.html
- SAP Cloud SDK material document service reference: https://javadoc.io/static/com.sap.cloud.sdk.s4hana/s4hana-api-odata/3.5.0/com/sap/cloud/sdk/s4hana/datamodel/odata/services/DefaultMaterialDocumentService.html

## Utility electricity

Researched format: ENERGY STAR Portfolio Manager meter and meter-consumption concepts, because it is a widely used building energy benchmark system and its web services model reflects real meter hierarchy.

What I learned: energy data hangs off properties/meters, meter records have type and unit of measure, and consumption records are tied to specific meters. The Portfolio Manager docs also make clear that billing/meter data is not always calendar-month aligned.

Sample data: `sample_data/utility_meter_export.csv` includes meter IDs, account numbers, tariffs, kWh/MWh units, and billing periods that can cross month boundaries.

What would break: PDF bill extraction, demand readings, net metering, shared meters, tariff-specific charge rows, and missing meter-to-facility mapping.

References:

- ENERGY STAR Portfolio Manager Get Meter API: https://portfoliomanager.energystar.gov/webservices/home/api/meter/meter/get
- ENERGY STAR Introduction to Exchanging Data: https://portfoliomanager.energystar.gov/pdf/reference/Introduction_to_Exchanging_Data_en_US.pdf

## Corporate travel

Researched format: SAP Concur expense report APIs and travel/expense documentation. The Reports v4 API shows report IDs, user IDs, context types, approval/payment states, dates, business purpose, currency, and amount fields.

What I learned: Concur data is report/user/context oriented, API access depends on scopes and product edition, and travel emissions often need enrichment because the expense line may not carry distance.

Sample data: `sample_data/concur_travel_expenses.csv` includes report-line IDs, expense types, employee names, airport/station codes, currency, and a missing-distance flight row.

What would break: OAuth setup, datacenter-specific URLs, itinerary duplication, cabin class, multi-leg flights, refunds, personal expenses, and receipt itemization.

References:

- SAP Concur Reports v4 API: https://developer.concur.com/api-reference/expense/expense-report/v4.reports.html
- SAP Concur Developer Center API reference: https://developer.concur.com/api-reference/
