# Bike Lifecycle Management System - User Manual

**Version**: 1.0.0
**Last Updated**: November 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [Bike Acquisition](#bike-acquisition)
5. [Inventory Management](#inventory-management)
6. [Bike Details & Information](#bike-details--information)
7. [Transfers Between Branches](#transfers-between-branches)
8. [Recording Sales](#recording-sales)
9. [Repair & Maintenance Tracking](#repair--maintenance-tracking)
10. [Reports & Analytics](#reports--analytics)
11. [Commission Tracking](#commission-tracking)
12. [User Roles & Permissions](#user-roles--permissions)
13. [Troubleshooting](#troubleshooting)
14. [FAQ](#faq)

---

## Introduction

### What is the Bike Lifecycle Management System?

The Bike Lifecycle Management System is a comprehensive solution for managing second-hand motorcycle sales operations across multiple companies and branches. It tracks the complete lifecycle of each bike from procurement through repairs, transfers, and final sale.

### Key Features

- **Bike Acquisition**: Record new bike purchases with complete details
- **Stock Management**: Track bikes across multiple branches and companies
- **Repair Tracking**: Monitor maintenance costs and service history
- **Transfer Management**: Move bikes between branches with approval workflow
- **Sales Recording**: Complete sales documentation with P/L tracking
- **Commission Calculation**: Automatic sales commission for staff
- **Reports & Analytics**: Comprehensive business intelligence reports
- **Cost Tracking**: Track all costs (purchase, repair, branch expenses)

### Who Should Use This System?

- **Branch Managers**: Manage daily operations, record sales, approve transfers
- **Procurement Staff**: Add new bikes to inventory
- **Mechanics**: Log repair jobs and costs
- **Finance Team**: Access reports and cost summaries
- **Administrators**: Manage users and system configuration

---

## Getting Started

### System Requirements

- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Screen Resolution**: 1366x768 minimum (1920x1080 recommended)
- **Internet Connection**: Broadband connection recommended

### Accessing the System

1. Open your web browser
2. Navigate to: `https://yourdomain.com`
3. You will see the login page

### Logging In

1. Enter your **username** provided by your administrator
2. Enter your **password**
3. Click **"Sign In"** button
4. You will be redirected to the dashboard

**First Login**: If this is your first time logging in, you may be prompted to change your password.

### Logging Out

Click your profile icon in the top right corner and select **"Logout"**.

---

## Dashboard Overview

The dashboard is your home screen after login. It provides a quick overview of your business operations.

### Dashboard Widgets

#### Total Bikes Card
- Shows total number of bikes in your inventory
- Color-coded status breakdown (In Stock, Sold, In Transit, etc.)

#### Active Transfers Card
- Number of bikes currently being transferred
- Quick link to transfers page

#### This Month's Sales Card
- Number of bikes sold this month
- Total revenue generated
- Quick link to sales page

#### Pending Actions Card
- Transfer requests awaiting approval
- Bikes requiring maintenance
- Other action items

### Quick Actions

Use the quick action buttons to:
- **+ Add New Bike**: Record a new bike acquisition
- **View Inventory**: Browse all bikes
- **Create Transfer**: Initiate a branch transfer
- **Record Sale**: Register a new sale

---

## Bike Acquisition

Bike acquisition is the process of adding a newly purchased bike to your inventory.

### Step-by-Step: Adding a New Bike

#### 1. Navigate to Acquisition Page

- Click **"Bikes"** in the main menu
- Select **"Acquisition"** from the dropdown
- Or use the **"+ Add New Bike"** quick action button

#### 2. Fill in Basic Information

**Company & Branch** (Required)
- Select your company (MA or IN)
- Select the branch where bike will be stored
- Business model defaults to "Second-Hand Sale"

**Bike Details** (Required)
- **Title**: Brief description (e.g., "Honda CB 125F 2020")
- **Brand**: Manufacturer (Honda, Yamaha, Bajaj, etc.)
- **Model**: Model name (CB 125F, FZ, Pulsar 150, etc.)
- **Year**: Manufacturing year (2018-2024)
- **Condition**: NEW or USED

**Identification**
- **License Plate**: Registration number (e.g., ABC-1234)
- **Engine Number**: Optional
- **Chassis Number**: Optional

#### 3. Purchase Information

**Financial Details** (Required)
- **Purchase Price**: Amount paid for the bike in LKR
- **Procurement Date**: When the bike was purchased

**Supplier Information**
- **Supplier Name**: Who you bought it from
- **Supplier Contact**: Phone number
- **Supplier Address**: Optional

**Transaction Details**
- **Procured By**: Staff member who made the purchase
- **Payment Method**: CASH, BANK, FINANCE, etc.
- **Invoice Number**: Reference number
- **Notes**: Any additional information

#### 4. Submit

Click **"Submit"** button to save the bike.

Upon successful submission:
- A **stock number** is automatically assigned (e.g., MA/WW/ST/2066)
- Bike appears in inventory with status "IN_STOCK"
- Success screen shows stock number and next actions

### Stock Number Format

Stock numbers follow this format: `{COMPANY}/{BRANCH}/ST/{NUMBER}`

Examples:
- `MA/WW/ST/2066` - Matara Company, Walasmulla Branch, Stock #2066
- `IN/HP/ST/0145` - India Company, Haputale Branch, Stock #0145

**Note**: Stock numbers are auto-generated and sequential per branch.

### Tips for Accurate Data Entry

✅ **Do's**:
- Always verify license plate before submitting
- Include supplier contact for future reference
- Add procurement notes if there are special conditions
- Double-check purchase price

❌ **Don'ts**:
- Don't leave required fields blank
- Don't use special characters in stock numbers
- Don't duplicate license plates

---

## Inventory Management

The inventory page shows all bikes across your authorized branches.

### Viewing Inventory

Navigate to: **Bikes > Inventory**

### Filtering Options

Use filters to narrow down the list:

**By Company**
- Select: MA, IN, or All

**By Branch**
- Select specific branch or "All Branches"
- You only see branches you have access to

**By Status**
- IN_STOCK: Available for sale
- SOLD: Already sold
- IN_TRANSIT: Being transferred
- ALLOCATED: Reserved for a customer
- MAINTENANCE: Under repair
- WRITTEN_OFF: Removed from inventory

**By Model**
- Filter by brand and model combination

**Search**
- Search by stock number, license plate, or bike title
- Example: "MA/WW/ST/2066" or "ABC-1234"

### Bike Grid View

Each bike card shows:
- Bike photo (if available)
- Stock number
- Brand and model
- Current status
- Purchase price
- Current location (branch)
- Action buttons (View, Transfer, Sell)

### Sorting

Click column headers to sort by:
- Stock number
- Brand
- Status
- Purchase price
- Procurement date

### Pagination

- Default: 20 bikes per page
- Use pagination controls at bottom to navigate
- Shows total count: "Showing 1-20 of 150 bikes"

### Actions from Inventory

**View Details**: Click bike card or "View" button to see full details

**Transfer**: Click "Transfer" to initiate branch transfer

**Sell**: Click "Sell" to record a sale (only for IN_STOCK bikes)

### Exporting Inventory

Click **"Export to Excel"** button to download:
- Complete inventory list
- Includes all filtered bikes
- Opens in Microsoft Excel or Google Sheets

---

## Bike Details & Information

Click any bike to view complete details and history.

### Overview Tab

**Bike Information**
- Stock number, brand, model, year
- Current status and location
- License plate and identification numbers

**Financial Summary**
- Purchase price
- Total repair costs
- Branch expenses
- Selling price (if sold)
- **Profit/Loss**: Automatically calculated

**Procurement Details**
- Who purchased the bike
- Supplier information
- Payment method
- Procurement date

### Cost Summary Tab

Detailed breakdown of all costs:

**Purchase Costs**
- Base purchase price
- Initial condition assessment

**Repair Costs**
- List of all repair jobs
- Parts and labor breakdown
- Mechanic assigned
- Job completion dates

**Branch Expenses**
- Storage fees
- Transportation costs
- Documentation fees
- Other miscellaneous expenses

**Total Investment**
```
Total Cost = Purchase Price + Repair Costs + Branch Expenses
```

**Profit/Loss** (for sold bikes)
```
Profit = Selling Price - Total Cost
```
- **Green**: Profitable sale
- **Red**: Loss-making sale

### Stock History Tab

Timeline of all events for this bike:

- 📦 **Procurement**: When bike was acquired
- 🔧 **Repairs**: Maintenance jobs completed
- 🚚 **Transfers**: Movement between branches
- 💰 **Sale**: Final sale transaction
- 📝 **Notes**: Additional events logged

Each event shows:
- Date and time
- User who performed action
- Location/branch
- Relevant details

### Transfers Tab

Shows all transfer requests for this bike:

**Pending Transfers**
- Awaiting approval
- Shows requested by, destination branch
- Action buttons: Approve/Reject

**Completed Transfers**
- Historical transfer records
- Includes approval chain
- Shows actual transfer dates

### Actions from Detail Page

**Edit Details**: Update bike information (if you have permission)

**Add Repair Job**: Log new maintenance work

**Initiate Transfer**: Move bike to another branch

**Record Sale**: Mark bike as sold

**Print Details**: Generate PDF report

---

## Transfers Between Branches

Transfers allow you to move bikes between branches with proper approval workflow.

### When to Use Transfers

- Moving inventory to balance stock across branches
- Fulfilling customer requests at specific branches
- Consolidating slow-moving inventory
- Responding to demand patterns

### Transfer Workflow

```
Request → Approval → In Transit → Delivered → Completed
```

### Creating a Transfer Request

#### 1. Navigate to Transfer Page

**Option A**: From inventory
- Find the bike you want to transfer
- Click **"Transfer"** button

**Option B**: From transfers page
- Go to **Bikes > Transfers**
- Click **"New Transfer Request"**
- Search for bike by stock number

#### 2. Fill Transfer Details

**Destination Branch** (Required)
- Select where bike should be sent
- Cannot be the same as current branch

**Transfer Reason**
- STOCK_REBALANCING: Evening out inventory
- CUSTOMER_REQUEST: Customer wants bike at their branch
- CONSOLIDATION: Combining stock
- MAINTENANCE: Sending for repairs
- OTHER: Specify in notes

**Requested By**
- Your name (auto-filled)

**Notes**
- Additional context for approver
- Special handling instructions

#### 3. Submit Request

Click **"Submit Transfer Request"**

The bike status changes to **"ALLOCATED"** and appears in pending transfers.

### Approving/Rejecting Transfers

**Who Can Approve**: Branch managers and administrators

**To Approve a Transfer**:
1. Go to **Bikes > Transfers**
2. Click **"Pending"** tab
3. Review transfer details
4. Click **"Approve"** or **"Reject"**
5. Add approval notes if needed

**After Approval**:
- Bike status changes to **"IN_TRANSIT"**
- Source branch sees bike as outgoing
- Destination branch sees bike as incoming

### Marking as Delivered

Once bike physically arrives at destination:

1. Destination branch manager clicks **"Mark as Delivered"**
2. Enter delivery date
3. Add delivery notes
4. Submit

**Result**:
- Bike status changes to **"IN_STOCK"**
- Current branch updates to destination
- New stock number assigned (if applicable)
- Transfer marked as **"COMPLETED"**

### Canceling a Transfer

**Before Approval**: Requester can cancel

**After Approval**: Only admin can cancel (requires justification)

### Transfer Views

**Pending Tab**
- Awaiting approval
- Shows requester, date, destination

**In Transit Tab**
- Approved and in motion
- Shows expected delivery date

**History Tab**
- All completed transfers
- Search by date range, branch, bike

### Transfer Reports

Generate transfer reports:
- By branch (incoming/outgoing)
- By date range
- By transfer reason
- Export to Excel

---

## Recording Sales

Record when a bike is sold to a customer.

### Prerequisites

- Bike must have status **"IN_STOCK"** or **"ALLOCATED"**
- You must have sales permission for the branch
- All repair work must be completed

### Step-by-Step: Recording a Sale

#### 1. Access Sale Form

**Option A**: From inventory
- Find the bike
- Click **"Sell"** button

**Option B**: From bike detail page
- Open bike details
- Click **"Record Sale"** button

**Option C**: From sales page
- Go to **Bikes > Sales**
- Click **"New Sale"**
- Search for bike

#### 2. Sale Information

**Sale Details** (Required)
- **Selling Price**: Final sale price in LKR
- **Sale Date**: When sale occurred (defaults to today)
- **Sold By**: Staff member (auto-filled)

**Customer Information** (Required)
- **Customer Name**: Full name
- **Customer Contact**: Phone number
- **Customer NIC**: National ID card number
- **Customer Address**: Full address

**Payment Details**
- **Payment Method**: CASH, BANK, FINANCE, INSTALLMENT
- **Down Payment**: If using finance (optional)
- **Finance Company**: If financed (optional)
- **Finance Amount**: Financed portion (optional)

**Trade-In** (Optional)
- **Trade-In Vehicle**: Details of customer's old bike
- **Trade-In Value**: Valuation amount

**Documentation**
- **Sale Invoice Number**: Invoice reference
- **Notes**: Any additional sale details

#### 3. Review Profit/Loss

Before submitting, review the P/L calculation:

```
Total Cost:
  Purchase Price:     LKR 150,000
  Repair Costs:       LKR  15,000
  Branch Expenses:    LKR   5,000
  ─────────────────────────────────
  Total:              LKR 170,000

Selling Price:        LKR 195,000

Profit/Loss:          LKR  25,000 ✓
```

- **Green (✓)**: Profitable sale
- **Red (✗)**: Loss (system may warn you)

#### 4. Submit Sale

Click **"Submit Sale"** button

**Result**:
- Bike status changes to **"SOLD"**
- Sale record created
- Commission calculated for seller
- Bike removed from active inventory
- Cannot be transferred or sold again

### After Recording Sale

- Print sale receipt
- Generate sale invoice
- Update commission ledger
- File documentation

### Editing a Sale

Sales can be edited within 24 hours by:
- The person who recorded the sale
- Branch manager
- Administrator

After 24 hours, only administrators can edit (requires approval).

### Canceling a Sale

To cancel a sale (rare):
1. Contact administrator
2. Provide justification
3. Admin reviews and approves
4. Bike returns to **"IN_STOCK"** status

---

## Repair & Maintenance Tracking

Track all repair and maintenance work done on bikes.

### Why Track Repairs?

- Accurate cost calculation
- Maintenance history for buyers
- Mechanic performance tracking
- Warranty management
- Profit/loss accuracy

### Adding a Repair Job

#### 1. Navigate to Bike Details

- Find bike in inventory
- Click to open details
- Go to **"Cost Summary"** tab

#### 2. Click "Add Repair Job"

#### 3. Fill Repair Details

**Job Information**
- **Job Type**: ROUTINE_MAINTENANCE, REPAIR, INSPECTION, CUSTOMIZATION
- **Description**: What work was done
- **Job Date**: When work was completed

**Costs**
- **Parts Cost**: Cost of spare parts used
- **Labor Cost**: Mechanic labor charges
- **Total Cost**: Auto-calculated (Parts + Labor)

**Assignment**
- **Mechanic**: Who performed the work
- **Job Status**: PENDING, IN_PROGRESS, COMPLETED, CANCELLED

**Details**
- **Parts Used**: List of spare parts
- **Work Notes**: Technical notes
- **Warranty**: If parts have warranty

#### 4. Submit

Job is logged and added to bike's total repair cost.

### Repair Job Statuses

- **PENDING**: Scheduled but not started
- **IN_PROGRESS**: Currently being worked on
- **COMPLETED**: Finished
- **CANCELLED**: Job cancelled (cost not applied)

### Viewing Repair History

On bike detail page, **Cost Summary** tab shows:
- All repair jobs chronologically
- Cost breakdown per job
- Total repair costs
- Mechanic performance

### Repair Reports

Generate reports for:
- Repair costs by bike
- Mechanic performance
- Most common repairs
- Cost trends over time

---

## Reports & Analytics

Access comprehensive business intelligence reports.

### Available Reports

#### 1. Acquisition Ledger

**Purpose**: Track all bike purchases

**Shows**:
- All bikes acquired in date range
- Purchase prices and suppliers
- Current status of each bike
- Total investment

**Filters**:
- Date range
- Company/branch
- Business model
- Supplier

**Export**: Excel, PDF

#### 2. Cost Summary Report

**Purpose**: Analyze profitability

**Shows**:
- Purchase costs
- Repair costs
- Branch expenses
- Selling prices
- Profit/loss per bike
- Aggregated totals

**Filters**:
- Date range
- Status (sold/unsold)
- Branch
- Profit/loss threshold

**Export**: Excel, PDF

**Key Metrics**:
- Total bikes
- Total investment
- Total revenue
- Average profit per bike
- Profit margin %

#### 3. Sales Report

**Purpose**: Track sales performance

**Shows**:
- All sales in date range
- Revenue generated
- Sales by staff member
- Sales by branch
- Commission earned

**Filters**:
- Date range
- Branch
- Sold by (staff)
- Payment method

**Export**: Excel, PDF

#### 4. Branch Stock Summary

**Purpose**: Monitor inventory levels

**Shows**:
- Current stock per branch
- Stock value
- Status distribution
- Aging analysis (how long in stock)

**Filters**:
- Branch
- Status
- Age threshold

**Export**: Excel, PDF

#### 5. Commission Report

**Purpose**: Calculate sales commissions

**Shows**:
- Sales per staff member
- Commission earned
- Payment status
- Total commissions owed

**Filters**:
- Date range
- Branch
- Staff member
- Payment status

**Export**: Excel, PDF

### Accessing Reports

1. Click **"Reports"** in main menu
2. Select report type
3. Set filters and date range
4. Click **"Generate Report"**
5. View on screen or export

### Scheduled Reports

Admins can schedule automatic reports:
- Daily sales summary
- Weekly inventory status
- Monthly P/L report
- Quarterly performance review

Reports are emailed to specified recipients.

---

## Commission Tracking

Track and manage sales commissions for staff.

### How Commissions Work

When a bike is sold:
1. System calculates profit/loss
2. Commission % is applied to profit (if profitable)
3. Commission amount credited to seller
4. Shows in commission ledger

### Commission Rates

Default rates (configurable by admin):
- Standard commission: 5% of profit
- Bonus tiers for high performers
- Special rates for difficult sales

### Viewing Your Commissions

Navigate to: **Reports > My Commissions**

**Shows**:
- Total commissions earned
- Pending payment
- Paid commissions
- Commission per sale

**Details per Sale**:
- Stock number
- Sale date
- Selling price
- Profit amount
- Commission earned
- Payment status

### Commission Payment

**Payment Cycle**: Monthly (configurable)

**Process**:
1. End of month: Commissions calculated
2. Finance review and approval
3. Payment processed
4. Status updated to "PAID"

**Payment Methods**:
- Bank transfer
- Cash
- Added to salary

### Commission Reports

**For Staff**:
- My commissions (current month)
- Payment history
- Year-to-date earnings

**For Managers**:
- Branch commission summary
- Top performers
- Commission expense tracking

---

## User Roles & Permissions

Different users have different access levels.

### User Roles

#### 1. Administrator
**Full system access**

Can:
- Manage users and roles
- Configure system settings
- Access all branches and companies
- Approve/reject all transactions
- View all reports
- Edit historical data
- Perform system maintenance

#### 2. Branch Manager
**Manage single or multiple branches**

Can:
- View inventory for assigned branches
- Approve transfers for their branches
- Record sales and acquisitions
- Add repair jobs
- View branch reports
- Manage branch staff

Cannot:
- Access other branches
- Change system configuration
- Delete historical records

#### 3. Sales Staff
**Record sales and basic operations**

Can:
- View inventory (read-only)
- Record sales for in-stock bikes
- Add procurement records
- View their own commissions
- Search bikes

Cannot:
- Approve transfers
- Edit other users' sales
- Access financial reports
- Manage users

#### 4. Mechanic
**Log repair work**

Can:
- View bikes assigned to them
- Add repair jobs
- Update job status
- View repair history

Cannot:
- Record sales
- View financial data
- Approve transfers

#### 5. Finance Team
**Access reports and financial data**

Can:
- View all reports
- Export financial data
- Review commission ledgers
- Generate custom reports
- View cost summaries

Cannot:
- Modify bike records
- Record sales
- Approve transfers

#### 6. Viewer (Read-Only)
**View-only access**

Can:
- View inventory
- View bike details
- View reports

Cannot:
- Modify any data
- Record transactions
- Export data

### Permission Matrix

| Feature | Admin | Branch Mgr | Sales | Mechanic | Finance | Viewer |
|---------|-------|------------|-------|----------|---------|--------|
| Add Bikes | ✓ | ✓ | ✓ | - | - | - |
| Record Sales | ✓ | ✓ | ✓ | - | - | - |
| Approve Transfers | ✓ | ✓ | - | - | - | - |
| Add Repair Jobs | ✓ | ✓ | ✓ | ✓ | - | - |
| View Reports | ✓ | ✓ | Limited | - | ✓ | ✓ |
| Export Data | ✓ | ✓ | - | - | ✓ | - |
| Manage Users | ✓ | - | - | - | - | - |
| System Config | ✓ | - | - | - | - | - |

---

## Troubleshooting

### Common Issues

#### Cannot Login

**Problem**: "Invalid username or password"

**Solutions**:
1. Verify username (case-sensitive)
2. Check Caps Lock is off
3. Request password reset from admin
4. Clear browser cache and try again

#### Bike Not Appearing in Inventory

**Problem**: Just added a bike but can't see it

**Solutions**:
1. Check filters - ensure "All Branches" selected
2. Check status filter - should include "IN_STOCK"
3. Wait 30 seconds and refresh page (cache)
4. Search by stock number directly

#### Cannot Record Sale

**Problem**: "Sell" button is grayed out

**Reasons**:
- Bike status is not IN_STOCK or ALLOCATED
- Bike is IN_TRANSIT (wait for delivery)
- You don't have permission for this branch
- Bike has pending transfer request

**Solutions**:
1. Check bike status on detail page
2. Cancel pending transfer if not needed
3. Contact branch manager for permission
4. Wait for transfer to complete

#### Transfer Stuck in Pending

**Problem**: Transfer not being approved

**Solutions**:
1. Check with destination branch manager
2. Ensure all details are filled correctly
3. Add more context in transfer notes
4. Contact approver directly
5. Escalate to administrator if urgent

#### Report Shows No Data

**Problem**: Report appears empty

**Solutions**:
1. Adjust date range (may be too narrow)
2. Remove filters (may be too restrictive)
3. Check you have access to selected branch
4. Wait for materialized view refresh (happens nightly)
5. Contact support if data should be there

#### Slow Performance

**Problem**: System is slow to load

**Solutions**:
1. Check your internet connection
2. Clear browser cache
3. Close unused browser tabs
4. Try a different browser
5. Report to IT if consistently slow

#### Export Not Working

**Problem**: Excel/PDF export fails

**Solutions**:
1. Check popup blocker settings
2. Ensure sufficient data to export
3. Try smaller date range
4. Disable browser extensions
5. Try different browser

---

## FAQ

### General Questions

**Q: How often is data backed up?**
A: Database is backed up daily at 3:00 AM. Retain backups for 30 days.

**Q: Can I access the system from my phone?**
A: Yes, the system is mobile-responsive. Works on phones and tablets.

**Q: How long do bikes stay in the system after being sold?**
A: Forever. Historical records are kept for reporting and audit purposes.

**Q: Can I undo a sale?**
A: Only within 24 hours and only by admin. Contact support immediately if you made a mistake.

### Stock Number Questions

**Q: Can I manually set a stock number?**
A: No, stock numbers are auto-generated to ensure uniqueness and consistency.

**Q: What if I run out of stock numbers?**
A: Stock numbers go up to 9999 per branch. System alerts when approaching limit.

**Q: Can I reuse stock numbers from sold bikes?**
A: No, stock numbers are permanent identifiers and cannot be reused.

### Transfer Questions

**Q: How long does a transfer take?**
A: Depends on approval speed and physical transport. Typically 1-3 days.

**Q: Can I transfer to multiple branches at once?**
A: No, one bike = one transfer at a time. Must complete before initiating another.

**Q: What happens if bike is damaged during transfer?**
A: Contact admin immediately. Transfer can be marked as problematic and investigated.

### Sales Questions

**Q: Can I offer discounts?**
A: Yes, set selling price lower than asking price. System shows if sale is profitable.

**Q: How do I handle trade-ins?**
A: Record trade-in details in sale form. Value is noted but doesn't affect P/L calculation directly.

**Q: What if customer pays in installments?**
A: Record total selling price and note payment method as INSTALLMENT. Track payments separately.

### Repair Questions

**Q: Can I add repair costs after bike is sold?**
A: Yes, but it won't affect the sale P/L. Best to add all costs before selling.

**Q: How do I handle warranty repairs?**
A: Add repair job but set cost to zero. Note in description it's under warranty.

**Q: Can I delete a repair job?**
A: Only admins can delete. If you made a mistake, contact your manager.

### Commission Questions

**Q: When do I get paid commissions?**
A: Monthly, typically within first week of following month.

**Q: What if sale is returned/cancelled?**
A: Commission is reversed. Will show as negative in next month's statement.

**Q: Do I earn commission on loss-making sales?**
A: No, commission is % of profit. No profit = no commission.

### Reporting Questions

**Q: Why don't I see today's sales in report?**
A: Some reports use materialized views refreshed nightly. Use "Sales" report for real-time data.

**Q: Can I schedule reports to be emailed?**
A: Yes, contact admin to set up scheduled reports.

**Q: What format are exports?**
A: Excel (.xlsx) and PDF. Choose based on your need.

---

## Getting Help

### Support Channels

**Option 1: Contact Your Branch Manager**
For day-to-day questions and common issues.

**Option 2: Submit Support Ticket**
Navigate to: **Help > Submit Ticket**
Include:
- Description of issue
- Steps to reproduce
- Screenshots if applicable
- Your username and branch

**Option 3: Call IT Support**
Phone: +94 XXX XXX XXX
Hours: Mon-Fri 9:00 AM - 5:00 PM

**Option 4: Email Support**
support@yourdomain.com
Response time: Within 24 hours

### Training Resources

- **Video Tutorials**: Available in Help menu
- **Training Sessions**: Monthly webinars for new features
- **User Guide PDF**: Download from Help > Documentation

---

## Appendix

### Glossary

**Acquisition**: The process of adding a new bike to inventory

**Stock Number**: Unique identifier assigned to each bike

**Business Model**: Type of business (SECOND_HAND_SALE, FINANCE, etc.)

**Materialized View**: Pre-computed database view for fast reporting

**P/L (Profit/Loss)**: Selling price minus total costs

**Branch**: Physical location where bikes are stored/sold

**Company**: Parent organization that owns multiple branches

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-18
**For Technical Support**: support@yourdomain.com
