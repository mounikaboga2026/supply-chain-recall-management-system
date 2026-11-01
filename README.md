Supply Chain Recall Management System

## 1. Project Overview

The Supply Chain Recall Management System is a Python-based application designed to manage product traceability and recall operations in a supply chain. It helps organizations track raw materials, monitor production batches, maintain lot genealogy, and identify affected products during a product recall.

The system provides information about raw materials used in manufacturing, supplier details, production batches, and finished products. It helps users trace products from raw material sources to final products, making recall management easier, faster, and more accurate.

## 2. Problem Statement

In traditional supply chain systems, tracking raw materials and identifying affected products during a recall can be difficult and time-consuming.

When a raw material is defective or contaminated, companies need to identify which production batches and finished products are affected.

This project addresses these challenges by providing a centralized system for material tracking, batch traceability, and recall management.

## 3. Objectives

- Track raw materials and supplier information.
- Maintain production batch records.
- Implement lot genealogy for material traceability.
- Identify finished products associated with affected raw materials.
- Manage product recall cases.
- Improve supply chain transparency and accuracy.
- Reduce manual tracking efforts.

## 4. Key Features

### Raw Material Management
Stores and manages raw material information, including material details, supplier information, and available quantities.

### Supplier Management
Maintains supplier records and helps track the sources of raw materials.

### Production Batch Tracking
Maintains production batch details and connects raw materials with manufactured products.

### Lot Genealogy
Tracks the relationship between raw material lots, production batches, and finished products. It helps identify which raw materials were used in a particular product.

### Recall Management
Allows users to create and manage recall cases when defective materials or products are identified.

### Product Traceability
Helps trace products backward to their raw material sources and forward to the finished products affected by a particular material lot.

### Data Visualization
Provides a user-friendly interface to view and understand supply chain information.

## 5. Technologies Used

- **Programming Language:** Python
- **Frontend / User Interface:** Streamlit
- **Data Processing:** Pandas
- **Data Visualization:** Matplotlib
- **Database / Storage:** As implemented in the project
- **Development Tool:** Visual Studio Code
- **Version Control:** Git and GitHub

## 6. System Workflow

1. Add raw material details into the system.
2. Maintain supplier information.
3. Record production batch details.
4. Connect raw material lots with production batches.
5. Generate lot genealogy information.
6. Identify products manufactured using specific raw material lots.
7. Create recall cases for affected materials or products.
8. Trace and review all affected products.

## 7. Advantages

- Improves product traceability.
- Makes recall identification easier.
- Reduces manual work.
- Helps identify affected production batches.
- Improves supply chain visibility.
- Supports better decision-making.

## 8. Future Enhancements

- Integrate barcode and QR code scanning.
- Add real-time supplier tracking.
- Implement email and SMS recall notifications.
- Add advanced analytics and dashboards.
- Integrate machine learning for risk prediction.
- Deploy the application on a cloud platform.

## 9. Installation and Execution

### Step 1: Clone the Repository

```bash
git clone <your-github-repository-url>
```

### Step 2: Open the Project Folder

```bash
cd supply-chain-recall-management-system
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
streamlit run app.py
```

### Step 5: Open the Application

The application will open in your browser. If it does not open automatically, visit:

```text
http://localhost:8501
```

## 10. Conclusion

The Supply Chain Recall Management System provides an organized approach to managing supply chain traceability and product recalls. By connecting raw materials, suppliers, production batches, and finished products, the system helps users identify affected products efficiently and supports better recall management.

## 11. Author

Developed as a Python project to demonstrate supply chain management, lot genealogy, and product traceability.
